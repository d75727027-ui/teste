from flask import Flask, jsonify, render_template_string, request, send_file
import requests
from fake_useragent import UserAgent
import uuid
import time
import re
import random
import string
import os
import logging
from io import BytesIO
from datetime import datetime
# Join : t.me/GatewayMaker
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = Flask(__name__)
approved_cards_storage = []
payment_failure_cards_storage = []
processing_queue = []
processing_lock = False
current_processing_index = 0
# Helper functions to prevent duplicate cards
def add_approved_card(card_data):
    """Add approved card to storage if it doesn't already exist"""
    for existing_card in approved_cards_storage:
        if existing_card['card'] == card_data['card'] and existing_card['domain'] == card_data['domain']:
            logger.debug(f"Card already exists in approved storage: {card_data['card']}")
            return False
    approved_cards_storage.append(card_data)
    logger.debug(f"Added approved card: {card_data['card']}")
    return True
def add_payment_failure_card(card_data):
    """Add payment failure card to storage if it doesn't already exist"""
    for existing_card in payment_failure_cards_storage:
        if existing_card['card'] == card_data['card'] and existing_card['domain'] == card_data['domain']:
            logger.debug(f"Card already exists in payment failure storage: {card_data['card']}")
            return False
    payment_failure_cards_storage.append(card_data)
    logger.debug(f"Added payment failure card: {card_data['card']}")
    return True
@app.route('/')
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AutoChecker API - DEVELOPER: @dark</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --primary: #6a11cb;
                --secondary: #2575fc;
                --accent: #ff6b6b;
                --dark: #1a1a2e;
                --light: #f5f5f5;
                --success: #4caf50;
                --error: #f44336;
                --warning: #ff9800;
                --glass: rgba(255, 255, 255, 0.1);
                --glass-border: rgba(255, 255, 255, 0.2);
            }
           
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
           
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
                min-height: 100vh;
                color: var(--light);
                overflow-x: hidden;
                position: relative;
            }
           
            .bg-animation {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: -1;
                overflow: hidden;
            }
           
            .bg-animation span {
                position: absolute;
                display: block;
                width: 20px;
                height: 20px;
                background: rgba(255, 255, 255, 0.2);
                animation: move 25s linear infinite;
                bottom: -150px;
            }
           
            .bg-animation span:nth-child(1) {
                left: 25%;
                width: 80px;
                height: 80px;
                animation-delay: 0s;
            }
           
            .bg-animation span:nth-child(2) {
                left: 10%;
                width: 20px;
                height: 20px;
                animation-delay: 2s;
                animation-duration: 12s;
            }
           
            .bg-animation span:nth-child(3) {
                left: 70%;
                width: 20px;
                height: 20px;
                animation-delay: 4s;
            }
           
            .bg-animation span:nth-child(4) {
                left: 40%;
                width: 60px;
                height: 60px;
                animation-delay: 0s;
                animation-duration: 18s;
            }
           
            .bg-animation span:nth-child(5) {
                left: 65%;
                width: 20px;
                height: 20px;
                animation-delay: 0s;
            }
           
            .bg-animation span:nth-child(6) {
                left: 75%;
                width: 110px;
                height: 110px;
                animation-delay: 3s;
            }
           
            .bg-animation span:nth-child(7) {
                left: 35%;
                width: 150px;
                height: 150px;
                animation-delay: 7s;
            }
           
            .bg-animation span:nth-child(8) {
                left: 50%;
                width: 25px;
                height: 25px;
                animation-delay: 15s;
                animation-duration: 45s;
            }
           
            .bg-animation span:nth-child(9) {
                left: 20%;
                width: 15px;
                height: 15px;
                animation-delay: 2s;
                animation-duration: 35s;
            }
           
            .bg-animation span:nth-child(10) {
                left: 85%;
                width: 150px;
                height: 150px;
                animation-delay: 0s;
                animation-duration: 11s;
            }
           
            @keyframes move {
                0% {
                    transform: translateY(0) rotate(0deg);
                    opacity: 1;
                    border-radius: 0;
                }
                100% {
                    transform: translateY(-1000px) rotate(720deg);
                    opacity: 0;
                    border-radius: 50%;
                }
            }
           
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
           
            header {
                text-align: center;
                padding: 40px 0;
                position: relative;
            }
           
            .logo {
                display: inline-block;
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 10px;
                background: linear-gradient(90deg, #fff, var(--accent));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                animation: glow 2s ease-in-out infinite alternate;
            }
           
            @keyframes glow {
                from {
                    text-shadow: 0 0 10px #fff, 0 0 20px #fff, 0 0 30px var(--primary);
                }
                to {
                    text-shadow: 0 0 20px #fff, 0 0 30px var(--secondary), 0 0 40px var(--secondary);
                }
            }
           
            .tagline {
                font-size: 1.2rem;
                margin-bottom: 20px;
                opacity: 0.9;
            }
           
            .designer {
                font-size: 0.9rem;
                opacity: 0.7;
                margin-bottom: 30px;
            }
           
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 10px;
                animation: pulse 2s infinite;
            }
           
            .status-online {
                background-color: var(--success);
            }
           
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
                }
                70% {
                    box-shadow: 0 0 0 10px rgba(76, 175, 80, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
                }
            }
           
            .tabs {
                display: flex;
                justify-content: center;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
           
            .tab {
                padding: 12px 25px;
                margin: 0 10px 10px;
                background: var(--glass);
                backdrop-filter: blur(10px);
                border: 1px solid var(--glass-border);
                border-radius: 30px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
            }
           
            .tab:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: translateY(-3px);
            }
           
            .tab.active {
                background: linear-gradient(90deg, var(--primary), var(--secondary));
                border: 1px solid transparent;
            }
           
            .tab-content {
                display: none;
            }
           
            .tab-content.active {
                display: block;
            }
           
            .glass-card {
                background: var(--glass);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid var(--glass-border);
                margin-bottom: 30px;
            }
           
            .form-group {
                margin-bottom: 20px;
            }
           
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
            }
           
            .form-control {
                width: 100%;
                padding: 15px;
                border-radius: 10px;
                border: 1px solid var(--glass-border);
                background: rgba(255, 255, 255, 0.05);
                color: white;
                font-family: 'Poppins', sans-serif;
                transition: all 0.3s ease;
            }
           
            .form-control:focus {
                outline: none;
                border-color: var(--primary);
                background: rgba(255, 255, 255, 0.1);
            }
           
            .form-control::placeholder {
                color: rgba(255, 255, 255, 0.7);
            }
           
            textarea.form-control {
                min-height: 150px;
                resize: vertical;
            }
           
            .btn {
                display: inline-block;
                padding: 12px 25px;
                border-radius: 10px;
                border: none;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
                font-family: 'Poppins', sans-serif;
                margin-right: 10px;
                margin-bottom: 10px;
            }
           
            .btn-primary {
                background: linear-gradient(90deg, var(--primary), var(--secondary));
                color: white;
            }
           
            .btn-primary:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
           
            .btn-secondary {
                background: var(--glass);
                color: white;
                border: 1px solid var(--glass-border);
            }
           
            .btn-secondary:hover {
                background: rgba(255, 255, 255, 0.2);
            }
           
            .btn-success {
                background: var(--success);
                color: white;
            }
           
            .btn-success:hover {
                background: #45a049;
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
           
            .btn-warning {
                background: var(--warning);
                color: white;
            }
           
            .btn-warning:hover {
                background: #e68900;
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
           
            .result-container {
                margin-top: 20px;
                padding: 20px;
                border-radius: 10px;
                background: rgba(0, 0, 0, 0.2);
                display: none;
            }
           
            .result-container.show {
                display: block;
            }
           
            .result-success {
                border-left: 5px solid var(--success);
            }
           
            .result-error {
                border-left: 5px solid var(--error);
            }
           
            .result-item {
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--glass-border);
            }
           
            .result-item.success {
                border-left: 5px solid var(--success);
            }
           
            .result-item.error {
                border-left: 5px solid var(--error);
            }
           
            .result-item.warning {
                border-left: 5px solid var(--warning);
            }
           
            .result-item.processing {
                border-left: 5px solid var(--warning);
            }
           
            .card-number {
                font-weight: 600;
                margin-bottom: 5px;
            }
           
            .card-response {
                margin-bottom: 5px;
            }
           
            .card-status {
                font-weight: 500;
            }
           
            .progress-bar {
                height: 5px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                margin-top: 10px;
                overflow: hidden;
            }
           
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--primary), var(--secondary));
                width: 0%;
                transition: width 0.3s ease;
            }
           
            .stats {
                display: flex;
                justify-content: space-around;
                margin-top: 20px;
            }
           
            .stat-item {
                text-align: center;
            }
           
            .stat-value {
                font-size: 1.5rem;
                font-weight: 600;
            }
           
            .stat-label {
                font-size: 0.9rem;
                opacity: 0.7;
            }
           
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 10px;
                color: white;
                font-weight: 500;
                transform: translateX(150%);
                transition: transform 0.3s ease;
                z-index: 1000;
                max-width: 300px;
            }
           
            .notification.show {
                transform: translateX(0);
            }
           
            .notification-success {
                background: var(--success);
            }
           
            .notification-error {
                background: var(--error);
            }
           
            .notification-info {
                background: var(--primary);
            }
           
            .loader {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 1s ease-in-out infinite;
                margin-right: 10px;
            }
           
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
           
            .copy-btn {
                background: var(--glass);
                border: 1px solid var(--glass-border);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.8rem;
                transition: all 0.3s ease;
            }
           
            .copy-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }
           
            .copy-btn.copied {
                background: var(--success);
            }
           
            .download-section {
                margin-top: 20px;
                padding: 20px;
                border-radius: 10px;
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid var(--glass-border);
            }
           
            .download-section h4 {
                margin-bottom: 15px;
            }
           
            .download-info {
                margin-bottom: 15px;
                padding: 10px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
            }
           
            .control-buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 15px;
            }
           
            footer {
                text-align: center;
                padding: 30px 0;
                margin-top: 50px;
                opacity: 0.7;
            }
           
            @media (max-width: 768px) {
                .container {
                    padding: 10px;
                }
               
                .glass-card {
                    padding: 20px;
                }
               
                .tabs {
                    flex-direction: column;
                    align-items: center;
                }
               
                .tab {
                    width: 80%;
                    text-align: center;
                }
               
                .stats {
                    flex-direction: column;
                }
               
                .stat-item {
                    margin-bottom: 15px;
                }
               
                .control-buttons {
                    flex-direction: column;
                }
            }
        </style>
    </head>
    <body>
        <div class="bg-animation">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
        </div>
       
        <div class="container">
            <header>
                <div class="logo">AutoChecker API</div>
                <div class="tagline">Advanced Cielo Payment Processing</div>
                <div class="designer">DEVELOPER: @dark</div>
                <div><span class="status-indicator status-online"></span>API Status: Online</div>
            </header>
           
            <div class="tabs">
                <div class="tab active" onclick="switchTab('single')">Single Checker</div>
                <div class="tab" onclick="switchTab('mass')">Mass Checker</div>
                <div class="tab" onclick="switchTab('api')">API Documentation</div>
            </div>
           
            <!-- Single Checker Tab -->
            <div id="single-tab" class="tab-content active">
                <div class="glass-card">
                    <h3>Single Card Checker</h3>
                    <div class="form-group">
                        <label for="single-site">Site Domain (Optional)</label>
                        <input type="text" id="single-site" class="form-control" placeholder="example.com">
                    </div>
                    <div class="form-group">
                        <label for="single-merchant-id">Cielo Merchant ID</label>
                        <input type="text" id="single-merchant-id" class="form-control" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx">
                    </div>
                    <div class="form-group">
                        <label for="single-merchant-key">Cielo Merchant Key</label>
                        <input type="text" id="single-merchant-key" class="form-control" placeholder="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX">
                    </div>
                    <div class="form-group">
                        <label for="single-cc">Card Details</label>
                        <input type="text" id="single-cc" class="form-control" placeholder="4242424242424242|12|25|123">
                    </div>
                    <button class="btn btn-primary" onclick="checkSingleCard()">
                        <span id="single-loader" style="display:none;" class="loader"></span>
                        Check Card
                    </button>
                    <button class="btn btn-secondary" onclick="clearSingleResults()">Clear Results</button>
                   
                    <div id="single-result" class="result-container">
                        <h4>Result:</h4>
                        <div id="single-result-content"></div>
                    </div>
                </div>
            </div>
           
            <!-- Mass Checker Tab -->
            <div id="mass-tab" class="tab-content">
                <div class="glass-card">
                    <h3>Mass Card Checker</h3>
                    <div class="form-group">
                        <label for="mass-site">Site Domain (Optional)</label>
                        <input type="text" id="mass-site" class="form-control" placeholder="example.com">
                    </div>
                    <div class="form-group">
                        <label for="mass-merchant-id">Cielo Merchant ID</label>
                        <input type="text" id="mass-merchant-id" class="form-control" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx">
                    </div>
                    <div class="form-group">
                        <label for="mass-merchant-key">Cielo Merchant Key</label>
                        <input type="text" id="mass-merchant-key" class="form-control" placeholder="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX">
                    </div>
                    <div class="form-group">
                        <label for="mass-cc">Card Details (One per line)</label>
                        <textarea id="mass-cc" class="form-control" placeholder="4242424242424242|12|25|123&#10;4000000000000002|12|25|123&#10;..."></textarea>
                    </div>
                   
                    <div class="control-buttons">
                        <button class="btn btn-primary" onclick="startMassCheck()" id="start-btn">
                            <span id="mass-loader" style="display:none;" class="loader"></span>
                            Start Check
                        </button>
                        <button class="btn btn-warning" onclick="pauseMassCheck()" id="pause-btn" style="display:none;">
                            <i class="fas fa-pause"></i> Pause
                        </button>
                        <button class="btn btn-secondary" onclick="stopMassCheck()" id="stop-btn" style="display:none;">
                            <i class="fas fa-stop"></i> Stop
                        </button>
                        <button class="btn btn-secondary" onclick="clearMassResults()">Clear All</button>
                        <button class="btn btn-success" onclick="downloadApprovedCards()" id="download-btn" style="display:none;">
                            <i class="fas fa-download"></i> Download Live
                        </button>
                        <button class="btn btn-warning" onclick="downloadPaymentFailureCards()" id="download-failure-btn" style="display:none;">
                            <i class="fas fa-download"></i> Download Sem Saldo
                        </button>
                    </div>
                   
                    <div id="mass-progress" class="progress-bar" style="display:none;">
                        <div id="mass-progress-fill" class="progress-fill"></div>
                    </div>
                   
                    <div id="mass-stats" class="stats" style="display:none;">
                        <div class="stat-item">
                            <div id="mass-total" class="stat-value">0</div>
                            <div class="stat-label">Total</div>
                        </div>
                        <div class="stat-item">
                            <div id="mass-approved" class="stat-value">0</div>
                            <div class="stat-label">Live</div>
                        </div>
                        <div class="stat-item">
                            <div id="mass-declined" class="stat-value">0</div>
                            <div class="stat-label">Died</div>
                        </div>
                        <div class="stat-item">
                            <div id="mass-processed" class="stat-value">0</div>
                            <div class="stat-label">Processed</div>
                        </div>
                        <div class="stat-item">
                            <div id="mass-current" class="stat-value">-</div>
                            <div class="stat-label">Current</div>
                        </div>
                    </div>
                   
                    <div id="mass-result" class="result-container">
                        <h4>Results:</h4>
                        <div id="mass-result-content"></div>
                    </div>
                   
                    <div id="download-section" class="download-section" style="display:none;">
                        <h4>Download Live Cards</h4>
                        <div id="download-info" class="download-info">
                            <p>Live cards will be saved automatically. Click the button above to download.</p>
                            <p id="approved-count">Live Cards: 0</p>
                        </div>
                    </div>
                </div>
            </div>
           
            <!-- API Documentation Tab -->
            <div id="api-tab" class="tab-content">
                <div class="glass-card">
                    <h3>API Documentation</h3>
                    <div class="result-item">
                        <h4>Single Card Processing</h4>
                        <p>Process a single card payment through Cielo</p>
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px; margin-top: 10px; font-family: monospace;">
                            /process?key=inferno&amp;merchant_id=your_merchant_id&amp;merchant_key=your_merchant_key&amp;site=example.com&amp;cc=card_number|mm|yy|cvv
                        </div>
                        <button class="copy-btn" onclick="copyToClipboard('/process?key=inferno&amp;merchant_id=your_merchant_id&amp;merchant_key=your_merchant_key&amp;site=example.com&amp;cc=card_number|mm|yy|cvv')">Copy</button>
                    </div>
                   
                    <div class="result-item">
                        <h4>Download Live Cards</h4>
                        <p>Download all live cards as a text file</p>
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px; margin-top: 10px; font-family: monospace;">
                            /download/approved
                        </div>
                        <button class="copy-btn" onclick="copyToClipboard('/download/approved')">Copy</button>
                    </div>
                   
                    <div class="result-item">
                        <h4>Download Sem Saldo Cards</h4>
                        <p>Download all cards without balance as a text file</p>
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px; margin-top: 10px; font-family: monospace;">
                            /download/payment-failure
                        </div>
                        <button class="copy-btn" onclick="copyToClipboard('/download/payment-failure')">Copy</button>
                    </div>
                   
                    <div class="result-item">
                        <h4>Health Check</h4>
                        <p>Check API status and availability</p>
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px; margin-top: 10px; font-family: monospace;">
                            /health
                        </div>
                        <button class="copy-btn" onclick="copyToClipboard('/health')">Copy</button>
                    </div>
                </div>
            </div>
           
            <footer>
                <p>&copy; 2026 AutoChecker API. All rights reserved. | DEVELOPER: @dark</p>
            </footer>
        </div>
       
        <div id="notification" class="notification"></div>
       
        <script>
            // Tab switching
            function switchTab(tabName) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
               
                // Remove active class from all tab buttons
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
               
                // Show selected tab
                document.getElementById(tabName + '-tab').classList.add('active');
               
                // Add active class to clicked tab button
                event.target.classList.add('active');
            }
           
            // Show notification
            function showNotification(message, type) {
                const notification = document.getElementById('notification');
                notification.textContent = message;
                notification.className = `notification notification-${type}`;
                notification.classList.add('show');
               
                setTimeout(() => {
                    notification.classList.remove('show');
                }, 3000);
            }
           
            // Copy to clipboard
            function copyToClipboard(text) {
                navigator.clipboard.writeText(text).then(() => {
                    showNotification('Copied to clipboard!', 'success');
                });
            }
           
            // Format card number for display
            function formatCardNumber(cardNumber) {
                if (cardNumber.length <= 4) return cardNumber;
                return cardNumber.substring(0, 4) + 'xxxxxxxxxxxx' + cardNumber.substring(cardNumber.length - 4);
            }
           
            // Check single card
            function checkSingleCard() {
                const site = document.getElementById('single-site').value.trim();
                const merchantId = document.getElementById('single-merchant-id').value.trim();
                const merchantKey = document.getElementById('single-merchant-key').value.trim();
                const cc = document.getElementById('single-cc').value.trim();
                const resultContainer = document.getElementById('single-result');
                const resultContent = document.getElementById('single-result-content');
                const loader = document.getElementById('single-loader');
               
                if (!merchantId || !merchantKey || !cc) {
                    showNotification('Please fill in Merchant ID, Merchant Key and Card Details', 'error');
                    return;
                }
               
                // Show loader
                loader.style.display = 'inline-block';
               
                // Clear previous results
                resultContent.innerHTML = '';
                resultContainer.classList.add('show');
                resultContainer.classList.remove('result-success', 'result-error');
               
                // Make API request
                fetch(`/process?key=inferno&site=${site}&merchant_id=${merchantId}&merchant_key=${merchantKey}&cc=${cc}`)
                    .then(response => response.json())
                    .then(data => {
                        // Hide loader
                        loader.style.display = 'none';
                       
                        // Display result
                        const cardParts = cc.split('|');
                        const cardNumber = cardParts[0];
                       
                        let itemClass = 'error';
                        if (data.Status === 'Live') itemClass = 'success';
                        else if (data.Status === 'Sem saldo') itemClass = 'warning';
                       
                        resultContent.innerHTML = `
                            <div class="result-item ${itemClass}">
                                <div class="card-number">Card: ${formatCardNumber(cardNumber)}</div>
                                <div class="card-response">Response: ${data.Response}</div>
                                <div class="card-status">Status: ${data.Status}</div>
                            </div>
                        `;
                       
                        if (data.Status === 'Live') {
                            resultContainer.classList.add('result-success');
                            showNotification('Card is live!', 'success');
                        } else if (data.Status === 'Sem saldo') {
                            resultContainer.classList.add('result-warning');
                            showNotification('Card has no balance', 'warning');
                        } else {
                            resultContainer.classList.add('result-error');
                            showNotification('Card died', 'error');
                        }
                    })
                    .catch(error => {
                        // Hide loader
                        loader.style.display = 'none';
                       
                        resultContent.innerHTML = `
                            <div class="result-item error">
                                <div class="card-response">Error: ${error.message}</div>
                            </div>
                        `;
                        resultContainer.classList.add('result-error');
                        showNotification('An error occurred', 'error');
                    });
            }
           
            // Clear single results
            function clearSingleResults() {
                document.getElementById('single-result').classList.remove('show');
                document.getElementById('single-site').value = '';
                document.getElementById('single-merchant-id').value = '';
                document.getElementById('single-merchant-key').value = '';
                document.getElementById('single-cc').value = '';
            }
           
            // Global variables for mass check
            let massCards = [];
            let currentSite = '';
            let currentMerchantId = '';
            let currentMerchantKey = '';
            let currentCardIndex = 0;
            let totalCards = 0;
            let approvedCards = 0;
            let declinedCards = 0;
            let processedCards = 0;
            let isChecking = false;
            let isPaused = false;
            let checkInterval = null;
           
            // Start mass check
            function startMassCheck() {
                const site = document.getElementById('mass-site').value.trim();
                const merchantId = document.getElementById('mass-merchant-id').value.trim();
                const merchantKey = document.getElementById('mass-merchant-key').value.trim();
                const ccText = document.getElementById('mass-cc').value.trim();
               
                if (!merchantId || !merchantKey || !ccText) {
                    showNotification('Please fill in Merchant ID, Merchant Key and Card Details', 'error');
                    return;
                }
               
                // Parse cards
                massCards = ccText.split('\\n').filter(card => card.trim());
               
                if (massCards.length === 0) {
                    showNotification('Please enter at least one card', 'error');
                    return;
                }
               
                if (massCards.length > 1100) {
                    showNotification('Maximum 1100 cards allowed', 'error');
                    return;
                }
               
                // Initialize variables
                currentSite = site;
                currentMerchantId = merchantId;
                currentMerchantKey = merchantKey;
                currentCardIndex = 0;
                totalCards = massCards.length;
                approvedCards = 0;
                declinedCards = 0;
                processedCards = 0;
                isChecking = true;
                isPaused = false;
               
                // Update UI
                document.getElementById('start-btn').style.display = 'none';
                document.getElementById('pause-btn').style.display = 'inline-block';
                document.getElementById('stop-btn').style.display = 'inline-block';
                document.getElementById('mass-loader').style.display = 'inline-block';
                document.getElementById('mass-progress').style.display = 'block';
                document.getElementById('mass-stats').style.display = 'flex';
               
                // Update stats
                updateStats();
               
                // Clear previous results
                document.getElementById('mass-result-content').innerHTML = '';
                document.getElementById('mass-result').classList.add('show');
               
                // Hide download section
                document.getElementById('download-section').style.display = 'none';
                document.getElementById('download-btn').style.display = 'none';
               
                // Start checking cards one by one
                checkNextCard();
            }
           
            // Check next card in queue
            function checkNextCard() {
                if (!isChecking || isPaused || currentCardIndex >= massCards.length) {
                    if (currentCardIndex >= massCards.length) {
                        finishMassCheck();
                    }
                    return;
                }
               
                const card = massCards[currentCardIndex];
                const resultContent = document.getElementById('mass-result-content');
               
                // Create result item
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item processing';
                resultItem.id = `card-${currentCardIndex}`;
                resultItem.innerHTML = `
                    <div class="card-number">Card ${currentCardIndex + 1}/${totalCards}: ${formatCardNumber(card.split('|')[0])}</div>
                    <div class="card-response">Processing...</div>
                    <div class="card-status">Status: Checking</div>
                `;
                resultContent.appendChild(resultItem);
               
                // Scroll to show new item
                resultItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
               
                // Update current card display
                document.getElementById('mass-current').textContent = `${currentCardIndex + 1}/${totalCards}`;
               
                // Make API request
                fetch(`/process_single?key=inferno&site=${currentSite}&merchant_id=${currentMerchantId}&merchant_key=${currentMerchantKey}&cc=${card}`)
                    .then(response => response.json())
                    .then(data => {
                        // Update result item
                        let itemClass = 'error';
                        if (data.Status === 'Live') itemClass = 'success';
                        else if (data.Status === 'Sem saldo') itemClass = 'warning';
                        resultItem.className = `result-item ${itemClass}`;
                        resultItem.innerHTML = `
                            <div class="card-number">Card ${currentCardIndex + 1}/${totalCards}: ${formatCardNumber(card.split('|')[0])}</div>
                            <div class="card-response">Response: ${data.Response}</div>
                            <div class="card-status">Status: ${data.Status}</div>
                        `;
                       
                        // Update stats
                        if (data.Status === 'Live') {
                            approvedCards++;
                        } else {
                            declinedCards++;
                        }
                        processedCards++;
                       
                        // Update progress and stats
                        updateProgress();
                        updateStats();
                       
                        // Move to next card
                        currentCardIndex++;
                       
                        // Check if we should continue
                        if (isChecking && !isPaused && currentCardIndex < massCards.length) {
                            // Wait 1 second before processing next card
                            setTimeout(checkNextCard, 1000);
                        } else if (currentCardIndex >= massCards.length) {
                            finishMassCheck();
                        }
                    })
                    .catch(error => {
                        // Update result item
                        resultItem.className = 'result-item error';
                        resultItem.innerHTML = `
                            <div class="card-number">Card ${currentCardIndex + 1}/${totalCards}: ${formatCardNumber(card.split('|')[0])}</div>
                            <div class="card-response">Error: ${error.message}</div>
                            <div class="card-status">Status: Error</div>
                        `;
                       
                        // Update stats
                        declinedCards++;
                        processedCards++;
                       
                        // Update progress and stats
                        updateProgress();
                        updateStats();
                       
                        // Move to next card
                        currentCardIndex++;
                       
                        // Check if we should continue
                        if (isChecking && !isPaused && currentCardIndex < massCards.length) {
                            // Wait 1 second before processing next card
                            setTimeout(checkNextCard, 1000);
                        } else if (currentCardIndex >= massCards.length) {
                            finishMassCheck();
                        }
                    });
            }
           
            // Update progress bar
            function updateProgress() {
                const progressFill = document.getElementById('mass-progress-fill');
                const progress = (processedCards / totalCards) * 100;
                progressFill.style.width = `${progress}%`;
            }
           
            // Update stats display
            function updateStats() {
                document.getElementById('mass-total').textContent = totalCards;
                document.getElementById('mass-approved').textContent = approvedCards;
                document.getElementById('mass-declined').textContent = declinedCards;
                document.getElementById('mass-processed').textContent = processedCards;
            }
           
            // Pause mass check
            function pauseMassCheck() {
                if (!isChecking) return;
               
                isPaused = !isPaused;
                const pauseBtn = document.getElementById('pause-btn');
               
                if (isPaused) {
                    pauseBtn.innerHTML = '<i class="fas fa-play"></i> Resume';
                    showNotification('Checking paused', 'warning');
                } else {
                    pauseBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
                    showNotification('Checking resumed', 'info');
                    // Continue checking
                    checkNextCard();
                }
            }
           
            // Stop mass check
            function stopMassCheck() {
                isChecking = false;
                isPaused = false;
               
                // Reset UI
                document.getElementById('start-btn').style.display = 'inline-block';
                document.getElementById('pause-btn').style.display = 'none';
                document.getElementById('stop-btn').style.display = 'none';
                document.getElementById('mass-loader').style.display = 'none';
               
                showNotification('Checking stopped', 'warning');
            }
           
            // Finish mass check
            function finishMassCheck() {
                isChecking = false;
                isPaused = false;
               
                // Update UI
                document.getElementById('start-btn').style.display = 'inline-block';
                document.getElementById('pause-btn').style.display = 'none';
                document.getElementById('stop-btn').style.display = 'none';
                document.getElementById('mass-loader').style.display = 'none';
                document.getElementById('mass-current').textContent = '-';
               
                // Show download section if there are approved cards
                if (approvedCards > 0) {
                    document.getElementById('download-btn').style.display = 'inline-block';
                    document.getElementById('download-section').style.display = 'block';
                    document.getElementById('approved-count').textContent = `Live Cards: ${approvedCards}`;
                }
               
                // Show payment failure download button
                document.getElementById('download-failure-btn').style.display = 'inline-block';
               
                showNotification(`Mass check completed! Live: ${approvedCards}, Died: ${declinedCards}`, 'info');
            }
           
            // Clear mass results
            function clearMassResults() {
                // Stop any ongoing check
                stopMassCheck();
               
                // Reset variables
                massCards = [];
                currentCardIndex = 0;
                totalCards = 0;
                approvedCards = 0;
                declinedCards = 0;
                processedCards = 0;
               
                // Clear UI
                document.getElementById('mass-result').classList.remove('show');
                document.getElementById('mass-site').value = '';
                document.getElementById('mass-merchant-id').value = '';
                document.getElementById('mass-merchant-key').value = '';
                document.getElementById('mass-cc').value = '';
                document.getElementById('mass-progress').style.display = 'none';
                document.getElementById('mass-stats').style.display = 'none';
                document.getElementById('download-section').style.display = 'none';
                document.getElementById('download-btn').style.display = 'none';
                document.getElementById('mass-progress-fill').style.width = '0%';
               
                // Reset buttons
                document.getElementById('start-btn').style.display = 'inline-block';
                document.getElementById('pause-btn').style.display = 'none';
                document.getElementById('stop-btn').style.display = 'none';
            }
           
            // Download approved cards
            function downloadApprovedCards() {
                // Make request to download endpoint
                window.open('/download/approved', '_blank');
                showNotification('Download started', 'success');
            }
           
            // Download payment failure cards
            function downloadPaymentFailureCards() {
                // Make request to download endpoint
                window.open('/download/payment-failure', '_blank');
                showNotification('Download started', 'success');
            }
        </script>
    </body>
    </html>
    """)
def get_card_brand(card_number):
    card_number = card_number.replace(' ', '')
    if re.match(r'^4[0-9]{12}(?:[0-9]{3})?$', card_number):
        return 'Visa'
    elif re.match(r'^(5[1-5][0-9]{14}|2(22[1-9][0-9]{12}|2[3-9][0-9]{13}|[3-6][0-9]{14}|7[0-1][0-9]{13}|720[0-9]{12}))$', card_number):
        return 'Master'
    elif re.match(r'^3[47][0-9]{13}$', card_number):
        return 'Amex'
    elif re.match(r'^(606282|3841[046]0)\d{10}(\d{3})?$', card_number):
        return 'Hipercard'
    elif re.match(r'^((5067|4576|4011)\d{12}|(431274|438935|451416|457631|457632|504175|627780|636297|636368)\d{10}(\d{3})?)$', card_number):
        return 'Elo'
    else:
        return None
#Main Function Niggas Do Not Copy It
def process_card_cielo(merchant_id, merchant_key, domain, ccx):
    logger.debug(f"Processing card with Cielo for domain: {domain}")
    ccx = ccx.strip()
    try:
        n, mm, yy, cvc = ccx.split("|")
    except ValueError:
        logger.error("Invalid card format")
        return {
            "Response": "Invalid card format. Use: NUMBER|MM|YY|CVV",
            "Status": "Died"
        }
   
    if len(yy) == 4:
        yy = yy[2:]
   
    brand = get_card_brand(n)
    if brand is None:
        logger.error("Unsupported card brand")
        return {"Response": "Unsupported card brand", "Status": "Died"}
   
    user_agent = UserAgent().random
    order_id = ''.join(random.choices(string.digits, k=8))
    amount = 500  # 5.00 BRL
   
    payload = {
        "MerchantOrderId": order_id,
        "Customer": {
            "Name": "Comprador Teste"
        },
        "Payment": {
            "Type": "CreditCard",
            "Amount": amount,
            "Installments": 1,
            "Capture": False,
            "CreditCard": {
                "CardNumber": n,
                "Holder": "Teste Holder",
                "ExpirationDate": f"{mm}/{yy}",
                "SecurityCode": cvc,
                "Brand": brand
            }
        }
    }
   
    headers = {
        'MerchantId': merchant_id,
        'MerchantKey': merchant_key,
        'Content-Type': 'application/json',
        'User-Agent': user_agent
    }
   
    url = "https://api.cieloecommerce.cielo.com.br/1/sales/"
   
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15, verify=False)
        if response.status_code not in [200, 201]:
            logger.error(f"API error: {response.text}")
            return {"Response": response.text, "Status": "Died"}
       
        data = response.json()
        if 'Payment' not in data:
            logger.error("Invalid response structure")
            return {"Response": "Invalid response", "Status": "Died"}
       
        payment = data['Payment']
        status = payment.get('Status')
        return_code = payment.get('ReturnCode', '')
        return_message = payment.get('ReturnMessage', '')
       
        if status in [1, 2]:
            # Live - Void the authorization
            payment_id = payment['PaymentId']
            cancel_url = f"https://api.cieloecommerce.cielo.com.br/1/sales/{payment_id}/void"
            cancel_response = requests.put(cancel_url, headers=headers, timeout=15, verify=False)
            logger.debug(f"Void response: {cancel_response.status_code}")
           
            card_data = {
                'card': ccx,
                'domain': domain,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'response': return_message,
                'status': 'Live'
            }
            add_approved_card(card_data)
            return {"Response": return_message, "Status": "Live"}
       
        elif status == 3:
            if return_code == '51':
                card_data = {
                    'card': ccx,
                    'domain': domain,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'response': return_message,
                    'status': 'Sem saldo'
                }
                add_payment_failure_card(card_data)
                return {"Response": return_message, "Status": "Sem saldo"}
            else:
                return {"Response": return_message, "Status": "Died"}
       
        else:
            return {"Response": "Unknown status", "Status": "Died"}
   
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return {"Response": str(e), "Status": "Died"}
@app.route('/process')
def process_request():
    try:
        key = request.args.get('key')
        domain = request.args.get('site', 'cielo')
        merchant_id = request.args.get('merchant_id')
        merchant_key = request.args.get('merchant_key')
        cc = request.args.get('cc')
       
        logger.debug(f"Process request: key={key}, domain={domain}, merchant_id={merchant_id}, cc={cc}")
       
        if key != "inferno":
            logger.error("Invalid API key")
            return jsonify({"error": "Invalid API key", "status": "Unauthorized"}), 401
       
        if not merchant_id or not merchant_key:
            logger.error("Missing Cielo credentials")
            return jsonify({"error": "Missing merchant_id or merchant_key", "status": "Bad Request"}), 400
       
        if not cc or not re.match(r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$', cc):
            logger.error(f"Invalid card format: {cc}")
            return jsonify({"error": "Invalid card format. Use: NUMBER|MM|YY|CVV", "status": "Bad Request"}), 400
       
        result = process_card_cielo(merchant_id, merchant_key, domain, cc)
       
        return jsonify({
            "Response": result.get("Response", "Unknown response"),
            "Status": result.get("Status", "Unknown status")
        })
    except Exception as e:
        logger.error(f"Process request error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}", "status": "Error"}), 500
@app.route('/process_single')
def process_single_request():
    try:
        key = request.args.get('key')
        domain = request.args.get('site', 'cielo')
        merchant_id = request.args.get('merchant_id')
        merchant_key = request.args.get('merchant_key')
        cc = request.args.get('cc')
       
        logger.debug(f"Process single request: key={key}, domain={domain}, merchant_id={merchant_id}, cc={cc}")
       
        if key != "inferno":
            logger.error("Invalid API key")
            return jsonify({"error": "Invalid API key", "status": "Unauthorized"}), 401
       
        if not merchant_id or not merchant_key:
            logger.error("Missing Cielo credentials")
            return jsonify({"error": "Missing merchant_id or merchant_key", "status": "Bad Request"}), 400
       
        if not cc or not re.match(r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$', cc):
            logger.error(f"Invalid card format: {cc}")
            return jsonify({"error": "Invalid card format. Use: NUMBER|MM|YY|CVV", "status": "Bad Request"}), 400
       
        result = process_card_cielo(merchant_id, merchant_key, domain, cc)
       
        import gc
        gc.collect()
       
        return jsonify({
            "Response": result.get("Response", "Unknown response"),
            "Status": result.get("Status", "Unknown status")
        })
    except Exception as e:
        logger.error(f"Process single request error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}", "status": "Error"}), 500
@app.route('/download/approved')
def download_approved_cards():
    try:
        if not approved_cards_storage:
            return jsonify({"error": "No live cards available", "status": "Not Found"}), 404
       
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"live_cards_{timestamp}.txt"
       
        file_content = f"AutoChecker API - Live Cards Report\n"
        file_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        file_content += f"Total Live Cards: {len(approved_cards_storage)}\n"
        file_content += "=" * 60 + "\n\n"
       
        for i, card in enumerate(approved_cards_storage, 1):
            file_content += f"[{i}] Card: {card['card']}\n"
            file_content += f" Domain: {card['domain']}\n"
            file_content += f" Status: {card['status']}\n"
            file_content += f" Response: {card['response']}\n"
            file_content += f" Time: {card['timestamp']}\n"
            file_content += "-" * 40 + "\n"
       
        file_obj = BytesIO(file_content.encode('utf-8'))
       
        return send_file(
            file_obj,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}", "status": "Error"}), 500
@app.route('/download/payment-failure')
def download_payment_failure_cards():
    try:
        if not payment_failure_cards_storage:
            return jsonify({"error": "No sem saldo cards to download", "status": "Not Found"}), 404
       
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"sem_saldo_cards_{timestamp}.txt"
       
        file_content = f"AutoChecker API - Sem Saldo Cards Report\n"
        file_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        file_content += f"Total Sem Saldo Cards: {len(payment_failure_cards_storage)}\n"
        file_content += "=" * 60 + "\n\n"
       
        for i, card in enumerate(payment_failure_cards_storage, 1):
            file_content += f"[{i}] Card: {card['card']}\n"
            file_content += f" Domain: {card['domain']}\n"
            file_content += f" Status: {card['status']}\n"
            file_content += f" Response: {card['response']}\n"
            file_content += f" Time: {card['timestamp']}\n"
            file_content += "-" * 40 + "\n"
       
        file_obj = BytesIO(file_content.encode('utf-8'))
       
        return send_file(
            file_obj,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
    except Exception as e:
        logger.error(f"Download sem saldo error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}", "status": "Error"}), 500
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "status": "Not Found"}), 404
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "status": "Error"}), 500
if __name__ == '__main__':
   
    port = int(os.environ.get('PORT', 8000))
   
    app.run(host='0.0.0.0', port=port, debug=False)
