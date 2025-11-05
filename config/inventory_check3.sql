    SELECT
        SUM(ohd.primary_transaction_quantity) AS available_quantity,
        item.item_number                      AS item_number,
        org.organization_code                 AS inv_organization_code,
        org.organization_id,
        subinv.secondary_inventory_name       AS secondary_inventory_name,
        bu.business_unit_name                 AS business_unit_name
    FROM
        fdi_idl_catalog.default.dw_inventory_item_d      item          /* Dim_DW_INVENTORY_ITEM_D */,
        fdi_idl_catalog.default.dw_inv_subinventory_d    subinv        /* Dim_DW_INV_SUBINVENTORY_D */,
        fdi_idl_catalog.default.dw_internal_org_d                org           /* Dim_DW_INV_ORGANIZATION_D_Inventory_Org */,
        fdi_idl_catalog.default.dw_inv_onhand_details_cf ohd           /* Fact_DW_INV_ONHAND_DETAILS_CF */,
        fdi_idl_catalog.default.dw_business_unit_d_tl    bu
    WHERE subinv.organization_id = ohd.organization_id
        AND subinv.secondary_inventory_name = ohd.subinventory_code
        AND org.organization_id = ohd.organization_id
        AND item.item_number = ?
        AND bu.business_unit_id = ohd.business_unit_id
        AND item.organization_id = ohd.organization_id
        AND org.organization_code      = "002"
        AND item.inventory_item_id = ohd.inventory_item_id
        AND org.inv_business_unit_id = bu.business_unit_id
        AND bu.business_unit_name = ?
    GROUP BY
        bu.business_unit_name,
        org.organization_code,
        subinv.secondary_inventory_name,
        org.organization_id,
        item.item_number;