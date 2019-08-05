from flask import Flask, request
import requests
import json
import time
import re
import os

#client_id = os.environ['SALESFORCE_CLIENT_ID']  # ~85 characters
#client_secret = os.environ['SALESFORCE_CLIENT_SECRET']  # ~19 characters
#salesforce_username = os.environ['SALESFORCE_USERNAME']  # email address
#salesforce_password = os.environ['SALESFORCE_PASSWORD']

client_id = os.environ.get('SALESFORCE_CLIENT_ID', 'client_id')  # ~85 characters
client_secret = os.environ.get('SALESFORCE_CLIENT_SECRET', 'secret')  # ~19 characters
salesforce_username = os.environ.get('SALESFORCE_USERNAME','username')  # email address
salesforce_password = os.environ.get('SALESFORCE_PASSWORD', 'pass')

salesforce_login_url = os.environ.get('SALESFORCE_LOGIN_URL', 'https://login.salesforce.com')

gui='''<html><head>
<script src="http://code.jquery.com/jquery-1.9.1.js"></script>
</head><body>
<font face="arial">
<h1>SalesForce Lead Entry Form</h1>
Salesforce backend: ''' + (salesforce_login_url if 'salesforce' in salesforce_login_url else 'virtual service ' + salesforce_login_url) + '''
<h2>Leads</h2>
<div id="log">
<div id="noleads">None</div>
</div>
<h2>Enter a new lead</h2>
<form id="f">
<div>
<label class="title">First name</label>
<br>
<input type="text" id="firstname" name="firstname">
<br>
</div>
<div>
<label class="title">Last name</label>
<br>
<input type="text" id="lastname" name="lastname">
<br>
</div>
<div>
<label class="title">Company</label>
<br>
<input type="text" id="company" name="company">
<br>
</div>
<div>
<label class="title">Phone Number</label>
<br>
<input type="text" id="phone" name="phone">
<br>
</div>
<div>
<input type="button" id="s" name="s" value="Create">
</form>
<script type="text/javascript">
$('#s').click(function() {
        $.ajax({
                'url': '/api/leads',
                'method': 'POST',
                'data': '{ "firstname": "' + $('#firstname').val() + '", "lastname": "' + $('#lastname').val() + '" , "company": "' + $('#company').val() + '" , "phone": "' + $('#phone').val() + '" }',
                'dataType': 'json',
                'success': function(x) {
                        $('#noleads').remove()
                        $('#log').append('<div>' + x['firstname'] + ' ' + x['lastname'] + ' from ' + x['company'] + ' (phone: ' + x['phone'] + ') (<a href="https://na50.salesforce.com/' + x['salesforce_id'] + '">salesforce id ' + x['salesforce_id'] + '</a>)</div>');
                }
        });

});
$(function() {
        $.ajax({
                'url': '/api/leads',
                'dataType': 'json',
                'success': function(data) {
                        $(data).each(function(i, x) {
                                $('#noleads').remove()
                                $('#log').append('<div>' + x['firstname'] + ' ' + x['lastname'] + ' from ' + x['company'] + ' (phone: ' + x['phone'] + ') (<a href="https://na50.salesforce.com/' + x['salesforce_id'] + '">salesforce id ' + x['salesforce_id'] + '</a>)</div>');
                        });
                }
        });
});
</script>
</font>
</body></html>
'''

app = Flask(__name__)
db = []
id = 1

salesforce_login_resource = '/services/oauth2/token'
salesforce_lead_resource = '/services/data/v20.0/sobjects/Lead/'


def escape(s):
    return requests.utils.quote(s)

	
@app.route("/")
def d():
    return gui


@app.route('/api/leads/<leadid>', methods=['GET'])
def c(leadid):
    return json.dumps([x for x in db if str(x['id']) == str(leadid)])


@app.route('/api/leads', methods=['GET'])
def b():
    return json.dumps(db)


@app.route('/api/leads', methods=['POST'])
def a():
    global id
    body = request.get_data()
    print 'body: %s' % body
    rv = json.loads(body)
    id += 1
    rv['id'] = id
    #if 'salesforce' in salesforce_login_url:
    url = salesforce_login_url + salesforce_login_resource
    print 'url: %s' % url
    r = requests.post(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data='grant_type=password&client_id=%s&client_secret=%s&username=%s&password=%s' % (client_id, client_secret, escape(salesforce_username), escape(salesforce_password)))
    if r.status_code >= 400:
        raise Exception('Error: %d %s' % (r.status_code, r.text))
    token = json.loads(r.text)['access_token']
    #salesforce_instance_url = json.loads(r.text)['instance_url']
    #else:
    #       token = '0000000000000000000000000000000'
    #       salesforce_instance_url = salesforce_login_url

    #url = salesforce_instance_url + salesforce_lead_resource
    url = salesforce_login_url + salesforce_lead_resource
    print 'url: %s' % url
    r = requests.post(url, data='{"FirstName":"%s","LastName":"%s","Company":"%s"}' % (rv['firstname'], rv['lastname'], rv['company']), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
    if r.status_code >= 400:
        raise Exception('Error: %d %s' % (r.status_code, r.text))
    rv['salesforce_id'] = json.loads(r.text)['id']
    db.append(rv)
    return json.dumps(rv)


@app.route('/debug',  methods=['GET'])
def debug():
	return "SALESFORCE_LOGIN_URL: {}".format(salesforce_login_url)


if __name__ == "__main__":
    app.run()
