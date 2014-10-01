#Publisher Toolkit

##DESCRIPTION

The Publisher Toolkit provides end-to-end guidance, specifications and scripts to submit digital content metadata into the Learning Registry which will be searchable via the Learning Registry Index.

##COMPONENTS

* LearningRegistryPublisherImplementerToolkit-v12.docx – A step by step guide to publishing into the Learning Registry using the provided scripts

* LRMI-JSONLD-Spec-v15.docs – The most recent community guidelines on the LRMI JSON-LD specification being used in the Learning Registry today.

* LRMI-Items-Import-Template.xlsx – The Excel template for both metadata items and standards (two tabs).  Each are related by the “url” field.  Please note, not all of these columns have to be populated.  If they are left blank, they will not be outputted in the resultant JSON-LD.  Also, if you add columns, they will be added to the JSON-LD (and recommend using schema.org as a guide).  Once this template is filled out, both the items and standards sheets will need to be exported to CSV files.

* lrmi-csv2jsonld.py – A Python script to convert the items CSV file to LRMI JSON-LD files.  These will be created one file per row in the CSV spreadsheet and outputted in the “data” directory.

* lr-bulk-publish.py – A Python script to bulk submit JSON files to the Learning Registry.  You’ll need to plug in your Learning Registry Oauth keys and modify submitter information (line 95) which is also covered in the implementer guide above.

##CONTRIBUTE

##LICENSING

Learning Register Publisher Toolkit is licensed under the Apache License, Version 2.0 by Actualize Technology, Inc. See LICENSE-2.0.txt for full license text and rights.

Contains work previously published by inBloom, also licensed under the the Apache License, Version 2.0.
