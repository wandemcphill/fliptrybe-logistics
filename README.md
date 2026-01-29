# 🛰️ FlipTrybe: Move Money. Move Goods.
**Version 1.1 // The 2026 Grid Protocol**

FlipTrybe is an industrial-grade escrow and logistics marketplace designed for high-trust asset handshakes. By tethering liquidity to physical proof-of-delivery (PoD), we ensure that money only moves when goods are verified.

---

## 🤝 The Handshake Lifecycle
The FlipTrybe protocol follows a four-stage neural synchronization:

1. **Signal Deployment:** A Merchant registers a physical asset on the Market Grid.
2. **The Handshake:** A Buyer locks liquidity in the Escrow Vault, generating a unique `Handshake ID`.
3. **Physical Transmission:** An HQ Overseer deploys a verified Pilot Node to transport the asset.
4. **Liquidity Release:** The Pilot uploads a PoD signal. The Buyer inspects and authorizes the vault release, transmitting funds to the Merchant.

---

## 🧬 System Architecture
The grid is built on a unified Flask-SQLAlchemy stack:

* **HQ Command Center (`admin.py`):** Oversees Identity (KYC), Pilot deployment, and Dispute mediation.
* **The Cockpit (`pilot_console.html`):** Mission-control for Pilots to track transit and upload proof.
* **Commercial Hub (`merchant_hub.html`):** Real-time monitoring of active inventory and locked liquidity.
* **The Vault (`main.py`):** Secure logic handling internal wallet balances and Paystack synchronization.

---

## 🚀 Deployment Sequence

### 1. Initialize the Environment
Ensure your local node is synchronized with the 2026 manifest:
```bash
# Bypass PowerShell Execution Policy if needed:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

.\venv\Scripts\activate
pip install -r requirements.txt