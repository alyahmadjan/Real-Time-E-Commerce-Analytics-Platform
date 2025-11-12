import os
import secrets
import string
from flask import Flask, request, redirect, session, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session security

# Read essential Shopify app config from environment variables
SHOPIFY_API_KEY = os.getenv('SHOPIFY_CLIENT_ID')
SHOPIFY_API_SECRET = os.getenv('SHOPIFY_CLIENT_SECRET')
SCOPES = os.getenv('SCOPE')  # e.g. 'read_products,read_orders,read_customers'
REDIRECT_URI = os.getenv('REDIRECT_URL')  # e.g. 'http://localhost:5000/auth/callback'

def generate_state_token(length=16):
    """Generate a random string for CSRF protection"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

@app.route('/auth')
def auth():
    shop = request.args.get('shop')
    if not shop:
        return "Missing shop parameter", 400

    # Generate and store state token to protect against CSRF attacks
    state = generate_state_token()
    session['oauth_state'] = state

    # Build Shopify OAuth authorization URL
    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={SHOPIFY_API_KEY}&"
        f"scope={SCOPES}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"state={state}"
    )
    return redirect(auth_url)

@app.route('/auth/callback')
def auth_callback():
    # Verify state token
    state = request.args.get('state')
    if not state or state != session.get('oauth_state'):
        return "Invalid state parameter", 403

    # Get authorization code and shop from query params
    code = request.args.get('code')
    shop = request.args.get('shop')
    if not code or not shop:
        return "Missing required parameters", 400

    # Exchange authorization code for access token
    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        'client_id': SHOPIFY_API_KEY,
        'client_secret': SHOPIFY_API_SECRET,
        'code': code
    }

    response = requests.post(token_url, json=payload)
    if response.status_code != 200:
        return f"Failed to get access token: {response.text}", 400

    token_data = response.json()
    access_token = token_data.get('access_token')

    if not access_token:
        return "No access token returned", 400

    # Here you would store the access token securely (e.g. in a database)
    # For demo purposes, we just return the token and shop info as JSON
    return jsonify({
        'access_token': access_token,
        'shop': shop,
        'scope': token_data.get('scope')
    })

if __name__ == '__main__':
    app.run(debug=True)
