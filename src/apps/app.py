# app.py — intake-driven create (no user item/qty picking)
import json, re, requests, streamlit as st

st.set_page_config(page_title="Agent Orchestrator (Streaming)", page_icon="🤖", layout="wide")
st.title("🤖 SCM - Sales Order Automation Agent")
st.caption("Master agent executes sub agents in serial with streaming logs and a LangGraph-style diagram.")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("🔧 Configuration")
    base_url = st.text_input("Base URL", value="http://0.0.0.0:8084").rstrip("/")
    timeout = st.number_input("HTTP Timeout (s)", value=60, min_value=1, max_value=600)
    st.markdown("---")
    st.subheader("Run server")
    st.code("streamlit run app.py --server.address 0.0.0.0 --server.port 8505")
    st.markdown("---")
    transaction_number = st.text_input("Transaction Number", value="R230_Sample_Order_ATOModel_232")

# ---------------- HTTP helpers ----------------
session = requests.Session()
def _url(path: str) -> str: return f"{base_url}{path if path.startswith('/') else '/' + path}"
def GET(path, **kw):  return session.get(_url(path), timeout=timeout, **kw)
def POST(path, **kw): return session.post(_url(path), timeout=timeout, **kw)

# ---------------- State ----------------
DEFAULT_BUS = ["US1 Business Unit", "EMEA1 Business Unit", "APAC1 Business Unit"]
DEFAULT_SKUS = ["AS6647431", "AS6647432", "AS6647433"]  # only for ultimate fallback

if "order_json" not in st.session_state:           st.session_state.order_json = {}   # final create payload
if "intake_bu"  not in st.session_state:           st.session_state.intake_bu  = None
if "last_create_result" not in st.session_state:   st.session_state.last_create_result = None

# ---------------- Parsers/Builders ----------------
def parse_order_from_intake(intake_resp, fallback_txn: str) -> dict:
    """Convert /orders/image output into a minimal create-order payload. No user item/qty input."""
    def _unwrap(x):
        if isinstance(x, dict) and "final_answer" in x: return x["final_answer"]
        return x
    raw = _unwrap(intake_resp)

    # Already shaped as create payload
    if isinstance(raw, dict) and raw.get("lines"):
        # capture BU name if present
        st.session_state.intake_bu = raw.get("BusinessUnit") or raw.get("BillToCustomer", {}).get("BusinessUnit")
        return raw

    # Common schema from intake: {"BusinessUnit": "...", "OrderItems": [{"Item":"AS..","Quantity":N}, ...]}
    if isinstance(raw, str):
        try:
            as_json = json.loads(raw)
            if isinstance(as_json, dict):
                bu = as_json.get("BusinessUnit") or as_json.get("BillToCustomer", {}).get("BusinessUnit")
                st.session_state.intake_bu = bu
                items = []
                for key in ("OrderItems", "Items", "Lines"):
                    if isinstance(as_json.get(key), list):
                        for it in as_json[key]:
                            sku = it.get("Item") or it.get("ProductNumber") or it.get("item_number")
                            qty = it.get("Quantity") or it.get("OrderedQuantity") or it.get("qty")
                            if sku and qty is not None:
                                items.append((str(sku), int(qty)))
                        break
                if items:
                    return build_create_payload(fallback_txn, bu or DEFAULT_BUS[0], items)
        except Exception:
            pass

        # Bullet/text fallback “… Item AS#### … Quantity/Required: N …”
        pat = re.compile(r"(?:Item\s*)?(?P<sku>AS\d+)\D+?(?:Required:\s*(?P<q1>\d+)|Quantity\s*[:=]\s*(?P<q2>\d+))", re.I)
        items = []
        for m in pat.finditer(raw):
            sku = m.group("sku"); qty = int(m.group("q1") or m.group("q2"))
            items.append((sku, qty))
        if items:
            st.session_state.intake_bu = st.session_state.intake_bu or DEFAULT_BUS[0]
            return build_create_payload(fallback_txn, st.session_state.intake_bu, items)

    # Ultimate fallback (should rarely trigger)
    st.session_state.intake_bu = st.session_state.intake_bu or DEFAULT_BUS[0]
    return build_create_payload(fallback_txn, st.session_state.intake_bu, [(DEFAULT_SKUS[0], 1)])

def build_create_payload(txn: str, bu_name: str, items: list[tuple[str, int]]) -> dict:
    payload = {
        "SourceTransactionNumber": txn,
        "SourceTransactionSystem": "OPS",
        "SourceTransactionId": txn,
        "TransactionalCurrencyCode": "USD",
        # Map BU name -> IDs here if needed
        "BusinessUnitId": 300000046987012,
        "RequestingBusinessUnitId": 300000046987012,
        "BuyingPartyNumber": "10060",
        "RequestedShipDate": "2018-09-19",
        "SubmittedFlag": "true",
        "FreezePriceFlag": "false",
        "FreezeShippingChargeFlag": "false",
        "FreezeTaxFlag": "false",
        "lines": []
    }
    for i, (sku, qty) in enumerate(items, start=1):
        payload["lines"].append({
            "SourceTransactionLineId": str(i),
            "SourceTransactionLineNumber": str(i),
            "SourceScheduleNumber": "1",
            "SourceTransactionScheduleId": "1",
            "OrderedUOMCode": "zzu",
            "OrderedQuantity": int(qty),
            "ProductNumber": str(sku),
            "FOBPoint": "Destination",
            "FreightTerms": "Add freight",
            "PaymentTerms": "30 Net",
            "ShipmentPriority": "High",
        })
    # record BU name for inventory prompt derivation
    payload["BusinessUnit"] = bu_name
    return payload

def build_inventory_prompt(order_json: dict) -> str:
    lines = order_json.get("lines", []) if isinstance(order_json, dict) else []
    item_numbers = [str(l.get("ProductNumber")) for l in lines if l.get("ProductNumber")]
    req_qty = [int(l.get("OrderedQuantity", 0)) for l in lines]
    bu = (order_json.get("BusinessUnit") or st.session_state.intake_bu or DEFAULT_BUS[0]).strip()
    if not item_numbers: item_numbers = [DEFAULT_SKUS[0]]
    if not req_qty: req_qty = [1]
    return f"Return per-item availability for item_numbers: {item_numbers}, item_required_quantity: {req_qty} and bu: {bu}"

# ---------------- Tools UI ----------------
st.subheader("🛠️ Tools")
st.caption("Wired to: /orders/image, /orders/inventory, /orders/create")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**1) Order Intake — Agent**")
    q_question = st.text_input("question", value="Get all information about the order")
    q_image = st.file_uploader("image", type=["png","jpg","jpeg"])

with col2:
    st.markdown("**2) Inventory Check — Agent**")
    # BU: if intake provided a BU, we lock to it; otherwise let user choose for inventory only
    if st.session_state.intake_bu:
        st.text_input("Business Unit (from intake)", value=st.session_state.intake_bu, disabled=True)
    else:
        chosen_bu = st.selectbox("Business Unit (for inventory)", options=DEFAULT_BUS, index=0)
        # store as provisional until intake comes in
        st.session_state.intake_bu = chosen_bu

with col3:
    st.markdown("**3) Create Sales Order — Agent**")
    # Show derived payload (read-only)
    st.markdown("**Create Order Payload (derived from intake)**")
    st.json(st.session_state.order_json or {"info": "Run Order Intake to populate"})

with col4:
    st.markdown("**4) Sales Order Email — Agent**")
    email_to = st.text_input("Email To", value="customer@example.com")
    email_subject = st.text_input("Email Subject", value="Your Sales Order Confirmation")
    email_note = st.text_area("Email Note", value="Thank you for your order. See details attached/included.")

st.markdown("---")

# ---------------- Diagram ----------------
diagram_placeholder = st.empty()
STATUS_PENDING, STATUS_RUNNING, STATUS_SUCCESS, STATUS_FAIL = "pending", "running", "success", "fail"

def render_graph(status_map):
    colors = {
        STATUS_PENDING: "#e5e7eb", STATUS_RUNNING: "#fde68a",
        STATUS_SUCCESS: "#bbf7d0", STATUS_FAIL: "#fecaca",
    }
    dot = [
        'digraph G {','rankdir="LR";','node [fontname="Helvetica"];',
        'A [label="Master Agent \\n OrderX Hub", shape="circle", style="filled", fillcolor="#e0e7ff"];'
    ]
    def add_tool(code, label, status):
        dot.append(f'{code} [label="{label}", shape="box", style="filled,rounded", fillcolor="{colors[status]}"];')
    add_tool("T1", "Order Intake\\n Agent", status_map.get("T1","pending"))
    add_tool("T2", "Inventory Check\\n Agent", status_map.get("T2","pending"))
    add_tool("T3", "Create Sales Order\\n Agent", status_map.get("T3","pending"))
    add_tool("T4", "Sales Order Email\\n Tool (via create)", status_map.get("T4","pending"))
    dot += ["A -> T1;", "T1 -> T2;", "T2 -> T3;", "T3 -> T4;", "}"]
    diagram_placeholder.graphviz_chart("\n".join(dot))

status_map = {"T1": STATUS_PENDING, "T2": STATUS_PENDING, "T3": STATUS_PENDING, "T4": STATUS_PENDING}
render_graph(status_map)

# ---------------- Logs + Execute ----------------
run_col, log_col = st.columns([1,2])
with run_col: run = st.button("🚀 Execute Master Agent - OrderX Hub")
with log_col:
    st.markdown("**Live Logs**"); log_area = st.empty()

def stream_log(line=None, reset=False):
    if reset or "log_lines" not in st.session_state: st.session_state["log_lines"] = []
    if line is not None: st.session_state["log_lines"].append(line)
    log_area.code("\n".join(st.session_state["log_lines"][-500:]))

def show_payload(title, payload):
    st.markdown(f"**{title}**")
    if isinstance(payload, (dict, list)): st.json(payload)
    else: st.code(str(payload)[:5000])

if run:
    stream_log(reset=True)

    # STEP 1: intake
    status_map["T1"] = STATUS_RUNNING; render_graph(status_map)
    stream_log("Step 1/4: Order_Intake_Agent — uploading image + question…")
    try:
        files = {"image": (q_image.name, q_image.getvalue(), q_image.type or "image/jpeg")} if q_image else None
        data = {"question": q_question}
        r1 = POST("/orders/image", files=files, data=data, headers={"accept":"application/json"})
        p1 = r1.json() if r1.headers.get("content-type","").startswith("application/json") else r1.text
        ok1 = r1.ok
        stream_log(f"Step 1 → HTTP {r1.status_code}")
        status_map["T1"] = STATUS_SUCCESS if ok1 else STATUS_FAIL; render_graph(status_map)
        show_payload("/orders/image response", p1)

        if ok1:
            derived = parse_order_from_intake(p1, transaction_number)
            st.session_state.order_json = derived
        else:
            stream_log("Halting due to failure in Step 1.")
    except Exception as e:
        status_map["T1"] = STATUS_FAIL; render_graph(status_map)
        stream_log(f"Step 1 error: {e}")

    # STEP 2: inventory
    if status_map["T1"] == STATUS_SUCCESS:
        status_map["T2"] = STATUS_RUNNING; render_graph(status_map)
        stream_log("Step 2/4: Inventory_Check_Agent — checking inventory …")
        try:
            inv_prompt = build_inventory_prompt(st.session_state.order_json)
            r2 = GET("/orders/inventory", params={"input_prompt": inv_prompt}, headers={"accept":"application/json"})
            p2 = r2.json() if r2.headers.get("content-type","").startswith("application/json") else r2.text
            ok2 = r2.ok
            stream_log(f"Step 2 → HTTP {r2.status_code}")
            status_map["T2"] = STATUS_SUCCESS if ok2 else STATUS_FAIL; render_graph(status_map)
            show_payload("/orders/inventory response", p2)
        except Exception as e:
            status_map["T2"] = STATUS_FAIL; render_graph(status_map)
            stream_log(f"Step 2 error: {e}")

    # STEP 3: create
    derived_id = transaction_number
    if status_map["T2"] == STATUS_SUCCESS:
        status_map["T3"] = STATUS_RUNNING; render_graph(status_map)
        stream_log("Step 3/4: Create_Sales_Order — creating order …")
        try:
            r3 = POST("/orders/create", json=st.session_state.order_json, headers={"Content-Type":"application/json","accept":"application/json"})
            p3 = r3.json() if r3.headers.get("content-type","").startswith("application/json") else r3.text
            ok3 = r3.ok
            stream_log(f"Step 3 → HTTP {r3.status_code}")
            status_map["T3"] = STATUS_SUCCESS if ok3 else STATUS_FAIL; render_graph(status_map)
            show_payload("/orders/create response", p3)
            st.session_state.last_create_result = p3
            try:
                if isinstance(p3, dict):
                    derived_id = p3.get("OrderNumber") or p3.get("id") or p3.get("SourceTransactionNumber") or derived_id
            except Exception:
                pass
        except Exception as e:
            status_map["T3"] = STATUS_FAIL; render_graph(status_map)
            stream_log(f"Step 3 error: {e}")

    # STEP 4: email (via create_order_agent)
    if status_map["T3"] == STATUS_SUCCESS:
        status_map["T4"] = STATUS_RUNNING; render_graph(status_map)
        stream_log("Step 4/4: Sales_Order_Email — invoking create_order_agent's email tool …")
        try:
            email_payload = {
                "action": "send_email",
                "saas_transaction_id": str(derived_id),
                "email_to": email_to,
                "subject": email_subject,
                "note": email_note,
                "context": st.session_state.last_create_result,
            }
            r4 = POST("/orders/create", json=email_payload, headers={"Content-Type":"application/json","accept":"application/json"})
            p4 = r4.json() if r4.headers.get("content-type","").startswith("application/json") else r4.text
            ok4 = r4.ok
            stream_log(f"Step 4 → HTTP {r4.status_code}")
            status_map["T4"] = STATUS_SUCCESS if ok4 else STATUS_FAIL; render_graph(status_map)
            show_payload("/orders/create (email) response", p4)
        except Exception as e:
            status_map["T4"] = STATUS_FAIL; render_graph(status_map)
            stream_log(f"Step 4 error: {e}")

    stream_log("Done.")
