# Evoodoo: Evolution + Odoo = ❤️

## Try it out now!

```bash
git clone git@github.com:dudanogueira/evoodoo.git
cd evoodoo
docker compose up -d
```


### CONFIGURING ODOO

Go to: http://localhost:8069 

Evo, Base Automations should already be installed

Let's create a new connector. Go to `Evo > New`

- Name: test
- Uuid: 76320171-94ec-455e-89c8-42995918fec6 (you can change it, but we need this in Evolution)
- URL: http://api:8080
- APIKEY: `1369429683C4C977415CAAFCCE10F7D57E11`
- Channel Manager: Select general.
- Automatic Added Partners: Select Yourself.


### CONFIGURING EVOLUTION
Now, acess Evolution at:

http://localhost:8080

Provide the global apikey: `1369429683C4C977415CAAFCCE10F7D57E11`

create a new instance called `test`:

configure the Events > Webhook:

- URL: http://crm:8069/evo/connector/76320171-94ec-455e-89c8-42995918fec6
- Webhook Base64: True
- Mark All

Save

Now back to Odoo, you should see a start button. Also, the QRCODE should be delivered on the #general channel.