import pandas as pd
import glob
import os

data_dir = r"c:\Users\Abcom\Downloads\scnv-agent\data\raw_tables"
csv_files = glob.glob(f"{data_dir}\\*.csv")

# Standard SAP to English business terms dictionary
sap_to_english = {
    'Mandt': 'Client',
    'Matnr': 'MaterialNumber',
    'Werks': 'Plant',
    'Lgort': 'StorageLocation',
    'Charg': 'Batch',
    'Bwtar': 'ValuationType',
    'Menge': 'Quantity',
    'Meins': 'BaseUnit',
    'Bwart': 'MovementType',
    'Mjahr': 'MaterialYear',
    'Lfgja': 'FiscalYear',
    'Mblnr': 'MaterialDocument',
    'Zeile': 'MaterialDocItem',
    'Posnr': 'ItemNumber',
    'Budat': 'PostingDate',
    'Budat Mkpf': 'PostingDate',
    'Erdat': 'CreatedOn',
    'Ernam': 'CreatedBy',
    'Erzet': 'CreatedAtTime',
    'Ersda': 'CreatedOn',
    'Lifnr': 'Vendor',
    'Kunnr': 'Customer',
    'Vbeln': 'DocumentNumber',
    'Ebeln': 'PurchasingDocument',
    'Ebelp': 'PurchasingItem',
    'Bukrs': 'CompanyCode',
    'Bukrs Vf': 'CompanyCode',
    'Vkorg': 'SalesOrganization',
    'Vtweg': 'DistributionChannel',
    'Vkbur': 'SalesOffice',
    'Land1': 'Country',
    'Name1': 'Name',
    'Regio': 'Region',
    'Lfart': 'DeliveryType',
    'Lfimg': 'DeliveryQuantity',
    'Ntgew': 'NetWeight',
    'Brgew': 'GrossWeight',
    'Gewei': 'WeightUnit',
    'Volum': 'Volume',
    'Voleh': 'VolumeUnit',
    'Mtart': 'MaterialType',
    'Matkl': 'MaterialGroup',
    'Netpr': 'NetPrice',
    'Netwr': 'NetValue',
    'Waerk': 'Currency',
    'Waers': 'Currency',
    'Kdmat': 'CustomerMaterial',
    'Bwkey': 'ValuationArea',
    'Lfmon': 'PostingPeriod',
    'Stprs': 'StandardPrice',
    'Peinh': 'PriceUnit',
    'Aufnr': 'OrderNumber',
    'Bname': 'UserName',
    'Shkzg': 'DebitCredit',
    'Vbtyp': 'DocumentCategory',
    'Auart': 'SalesDocumentType',
    'Plifz': 'PlannedDeliveryTime',
    'Dismm': 'MRPType',
    'Dispo': 'MRPController',
    'Bedat': 'PO_Date',
    'Aedat': 'ChangedOn',
    'Bstnk': 'CustomerReference',
    'Tknum': 'ShipmentNumber',
    'Daten': 'Date',
    'Tpnum': 'ShipmentItem',
    # Adding some others that appeared in our list
    'Kkber': 'CreditControlArea',
    'Lbkum': 'TotalValuatedStock',
    'Vprsv': 'PriceControl',
    'Verpr': 'MovingAveragePrice',
    'Salk3': 'ValueTotalValuatedStock',
    'Route': 'Route',
    'Pstyv': 'ItemCategory',
    'Lfdat': 'DeliveryDate',
    'Wadat_Ist': 'ActualGI_Date',
    'Wadat': 'PlannedGI_Date'
}

print("Starting to rename columns in CSV files...")

for file in csv_files:
    basename = os.path.basename(file)
    print(f"Processing {basename}...")
    try:
        df = pd.read_csv(file)
        
        # Rename columns using our dictionary. If a column isn't in dict, keep original.
        new_cols = []
        changed = False
        for col in df.columns:
            if col in sap_to_english:
                new_cols.append(sap_to_english[col])
                changed = True
            else:
                new_cols.append(col)
                
        if changed:
            df.columns = new_cols
            df.to_csv(file, index=False)
            print(f"  -> Renamed columns and saved {basename}")
        else:
            print(f"  -> No columns needed translation in {basename}")
            
    except Exception as e:
        print(f"  -> Error processing {file}: {e}")

print("All files processed.")
