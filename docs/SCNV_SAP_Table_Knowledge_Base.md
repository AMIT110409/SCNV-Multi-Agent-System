# SAP Table Knowledge Base (SCNV Prototype)

This Knowledge Base is designed to help junior developers understand the specific data sources used to build the SCNV Supply Chain Visibility engine.

---

## 1. Master Data (Static Foundations)
These tables store the "Identity" of things. They don't change often.

| File Name | SAP Table Name | Description | Key Knowledge |
|-----------|----------------|-------------|---------------|
| **MARA.xlsx** | MARA | **General Material Data** | The identity of the product (Material #, Weight, UOM). |
| **MARC.xlsx** | MARC | **Plant Data for Material** | Rules for a product AT a specific location (Lead times, MRP types). |
| **KNA1.xlsx** | KNA1 | **Customer Master** | Name and location of the customers we sell to. |
| **LFA1.xlsx** | LFA1 | **Vendor Master** | Name and location of the suppliers we buy from. |
| **T001W.xlsx**| T001W | **Plant Master** | The physical address and country of our factories/warehouses. |
| **T001.xlsx** | T001 | **Company Code** | High-level financial entity (e.g., AB InBev Germany). |
| **TVKOT.xlsx**| TVKOT | **Sales Org Texts** | Human-readable names for Sales Organizations. |
| **T156.xlsx** | T156 | **Movement Type Data**| Defines how stock moves (Receipt vs Issue indicators). |

---

## 2. Inventory & Stock moves (Transactional)
The "Heartbeat" of SCNV. These record physical movement.

| File Name | SAP Table Name | Description | Key Knowledge |
|-----------|----------------|-------------|---------------|
| **MKPF.xlsx** | MKPF | **Material Doc Header** | The timestamp and user info for every stock move. |
| **MSEG.xlsx** | MSEG | **Material Doc Item** | The specific quantity, batch, and plant for every move. |
| **MCHA.xlsx** | MCHA | **Batches** | Detailed metadata for each batch (Shelf life, Manufacture date). |
| **MCHB.xlsx** | MCHB | **Batch Stocks** | Current available stock levels for each batch. |
| **MBEW.xlsx** | MBEW | **Material Valuation** | The financial value/price of the material. |
| **MBEWH.xlsx**| MBEWH | **Valuation History** | Historical prices of materials over time. |

---

## 3. Purchasing & Inbound (Sourcing)
These track "Incoming" promises and stock.

| File Name | SAP Table Name | Description | Key Knowledge |
|-----------|----------------|-------------|---------------|
| **EKKO.xlsx** | EKKO | **PO Header** | The agreement with the Vendor (Vendor #, Date). |
| **EKPO.xlsx** | EKPO | **PO Item** | The specific items ordered (Material, Price, Quantity). |
| **EKET.xlsx** | EKET | **Scheduling Agreement**| The expected arrival dates for the PO items. |

---

## 4. Sales & Outbound (Delivery)
These track how we fulfill customer orders.

| File Name | SAP Table Name | Description | Key Knowledge |
|-----------|----------------|-------------|---------------|
| **VBAK.xlsx** | VBAK | **Sales Header** | The customer's order info (Order Number, Customer #). |
| **VBAP.xlsx** | VBAP | **Sales Item** | The specific products the customer wants. |
| **LIKP.xlsx** | LIKP | **Delivery Header** | The document created to ship the goods. |
| **LIPS.xlsx** | LIPS | **Delivery Item** | The actual quantity and batch being put on the truck. |
| **VTTK.xlsx** | VTTK | **Shipment Header** | Logistics info (Truck ID, Shipping dates). |
| **VTTP.xlsx** | VTTP | **Shipment Item** | Which deliveries are grouped inside which shipment. |

---

## 5. Production & Manufacturing
Tracks how raw materials become products.

| File Name | SAP Table Name | Description | Key Knowledge |
|-----------|----------------|-------------|---------------|
| **AFKO.xlsx** | AFKO | **Production Order** | The roadmap for making a product (Work Order info). |

---

## 6. Custom SCNV Logic Sources
Specific files used for the prototype's unique features.

| File Name | Description | Key Knowledge |
|-----------|-------------|---------------|
| **P92_Milk_Ride.xlsx** | Milk Run Logistics | Tracks consolidated truck routes ("Milk Runs"). |
| **ZMD_BULK_MAIN.xlsx**| Bulk Material Master| Specific data for bulk liquid handling (often in brewery use cases). |
| **USR02 / USR21** | User Data | SAP user IDs used to track who posted which document. |

---

## How SCNV Prototypes These Tables

1.  **The Linker**: We use **`MSEG`** to find a Batch.
2.  **The Context**: We join **`MARA`** to see what the product is.
3.  **The Source**: We join **`EKKO`** to see which Vendor provided it.
4.  **The Destination**: We join **`VBAK`** to see which Customer it went to.
5.  **The Trace**: We follow the **Batch Number** across all these documents to draw the supply chain map.
