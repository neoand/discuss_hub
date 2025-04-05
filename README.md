
<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->
[![Pre-commit Status](https://github.com/dudanogueira/evoodoo/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/dudanogueira/evoodoo/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/dudanogueira/evoodoo/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/dudanogueira/evoodoo/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/dudanogueira/evoodoo/branch/18.0/graph/badge.svg)](https://codecov.io/gh/dudanogueira/evoodoo)
<!-- /!\ Non OCA Context : Set here the badge of your translation instance. -->

<!-- /!\ do not modify above this line -->

# Evoodoo

Integrate third party message channels into Odoo's discuss

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

This part will be replaced when running the oca-gen-addons-table script from OCA/maintainer-tools.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Dudatende / Duda Nogueira
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
asdasd
## How to Configure

First, run docker.

Create an instance in Evolution.

```bash
curl --request POST \
  --url http://localhost:8080/instance/create \
  --header 'Content-Type: application/json' \
  --header 'apikey: 1369429683C4C977415CAAFCCE10F7D57E11' \
  --data '{
    "instanceName": "test",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS",
    "webhook": {
			"url": "http://odoo:8069/evoodoo/connector/76320171-94ec-455e-89c8-42995918fec6",
			"base64": true,
         "events": [
             "APPLICATION_STARTUP",
             "QRCODE_UPDATED",
             "MESSAGES_SET",
             "MESSAGES_UPSERT",
             "MESSAGES_UPDATE",
             "MESSAGES_DELETE",
             "SEND_MESSAGE",
             "CONTACTS_SET",
            "CONTACTS_UPSERT",
             "CONTACTS_UPDATE",
             "PRESENCE_UPDATE",
             "CHATS_SET",
             "CHATS_UPSERT",
             "CHATS_UPDATE",
             "CHATS_DELETE",
             "GROUPS_UPSERT",
             "GROUP_UPDATE",
             "GROUP_PARTICIPANTS_UPDATE",
             "CONNECTION_UPDATE",
             "LABELS_EDIT",
             "LABELS_ASSOCIATION",
             "CALL",
             "TYPEBOT_START",
             "TYPEBOT_CHANGE_STATUS"
         ]
     }
}'
```