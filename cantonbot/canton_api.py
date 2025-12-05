"""
Модуль для работы с Canton Network Lighthouse API
"""
import requests
from typing import Dict, List, Optional
from urllib.parse import quote
from config import CANTON_API_BASE_URL

# Explorer URL for links
EXPLORER_URL = "https://remindnation.tech/explorer"


class CantonAPI:
    """Класс для взаимодействия с Canton Network API"""
    
    def __init__(self, base_url: str = CANTON_API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'CantonBot/1.0'
        })
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Выполняет GET запрос к API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def get_stats(self) -> Dict:
        """Получает статистику сети"""
        return self._get('/stats')
    
    def get_validators(self) -> Dict:
        """Получает список валидаторов"""
        return self._get('/validators')
    
    def get_rounds(self, page: int = 1, limit: int = 20) -> Dict:
        """Получает список раундов"""
        params = {'page': page, 'limit': limit}
        return self._get('/rounds', params=params)
    
    def get_governance(self, page: int = 1, limit: int = 20) -> Dict:
        """Получает список governance"""
        params = {'page': page, 'limit': limit}
        return self._get('/governance', params=params)
    
    def get_governance_details(self, governance_id: str) -> Dict:
        """Получает детали governance по ID"""
        return self._get(f'/governance/{governance_id}')
    
    def get_transaction_details(self, tx_id: str) -> Dict:
        """Получает детали транзакции по ID"""
        return self._get(f'/transactions/{tx_id}')
    
    def get_party_info(self, party_id: str) -> Dict:
        """Получает информацию о партии по ID"""
        # URL-encode party_id to handle special characters like ::
        encoded_party_id = quote(party_id, safe='')
        return self._get(f'/parties/{encoded_party_id}')
    
    def get_party_transactions(self, party_id: str, limit: int = 20) -> Dict:
        """Получает транзакции партии"""
        # First, get party info to extract numeric ID
        party_info = self.get_party_info(party_id)
        if 'error' in party_info:
            return party_info
        
        # Extract numeric ID from party info
        numeric_id = party_info.get('id')
        if not numeric_id:
            return {'error': 'Numeric ID not found in party info'}
        
        # Use numeric ID for transactions endpoint
        params = {'limit': limit}
        return self._get(f'/parties/{numeric_id}/tx', params=params)
    
    def get_party_transfers(self, party_id: str, limit: int = 20) -> Dict:
        """Получает трансферы партии"""
        # First, get party info to extract numeric ID
        party_info = self.get_party_info(party_id)
        if 'error' in party_info:
            return party_info
        
        # Extract numeric ID from party info
        numeric_id = party_info.get('id')
        if not numeric_id:
            return {'error': 'Numeric ID not found in party info'}
        
        # Use numeric ID for transfers endpoint
        params = {'limit': limit}
        return self._get(f'/parties/{numeric_id}/transfers', params=params)
    
    def _safe_float(self, value, default=0.0):
        """Safely converts value to float"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                return float(value.replace(',', ''))
            return default
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default=0):
        """Safely converts value to int"""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str):
                # Remove commas and convert
                return int(float(value.replace(',', '')))
            return default
        except (ValueError, TypeError):
            return default
    
    def _format_balance(self, value):
        """Formats balance with 2 decimal places"""
        try:
            if isinstance(value, (int, float)):
                return f"{float(value):,.2f}"
            elif isinstance(value, str):
                return f"{float(value.replace(',', '')):,.2f}"
            return str(value)
        except (ValueError, TypeError):
            return str(value)
    
    def _is_balance_field(self, key):
        """Checks if field name suggests it's a balance/amount field"""
        balance_keywords = ['balance', 'amount', 'value', 'cc', 'reward', 'stake', 'transfer', 'deposit', 'withdraw']
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in balance_keywords)
    
    def format_stats(self, stats: Dict) -> str:
        """Formats statistics for sending to Telegram"""
        if 'error' in stats:
            return f"❌ Error getting statistics: {stats['error']}"
        
        text = "📊 <b>Canton Network Statistics</b>\n\n"
        
        # Format main statistics
        if 'total_cc' in stats:
            total_cc = self._safe_float(stats['total_cc'])
            text += f"💰 <b>Total CC:</b> {total_cc:,.2f}\n"
        if 'total_reward' in stats:
            total_reward = self._safe_float(stats['total_reward'])
            text += f"🎁 <b>Total Reward:</b> {total_reward:,.2f}\n"
        if 'cc_price' in stats:
            cc_price = self._safe_float(stats['cc_price'])
            text += f"💵 <b>CC Price:</b> ${cc_price:.6f}\n"
        if 'total_validator' in stats:
            total_validator = self._safe_int(stats['total_validator'])
            text += f"🔐 <b>Total Validators:</b> {total_validator:,}\n"
        if 'total_sv' in stats:
            total_sv = self._safe_int(stats['total_sv'])
            text += f"⭐ <b>Total SV:</b> {total_sv:,}\n"
        if 'total_transaction' in stats:
            total_transaction = self._safe_int(stats['total_transaction'])
            text += f"💸 <b>Total Transactions:</b> {total_transaction:,}\n"
        if 'total_parties' in stats:
            total_parties = self._safe_int(stats['total_parties'])
            text += f"👥 <b>Total Parties:</b> {total_parties:,}\n"
        if 'version' in stats:
            text += f"🔢 <b>Version:</b> {stats['version']}\n"
        if 'migration' in stats:
            migration = self._safe_int(stats['migration'])
            text += f"🔄 <b>Migration:</b> {migration}\n"
        if 'featured_app_count' in stats:
            featured_app_count = self._safe_int(stats['featured_app_count'])
            text += f"⭐ <b>Featured Apps:</b> {featured_app_count}\n"
        
        # Add other fields
        for key, value in stats.items():
            if key not in ['total_cc', 'total_reward', 'cc_price', 'total_validator', 
                          'total_sv', 'total_transaction', 'total_parties', 'version', 
                          'migration', 'featured_app_count', 'durations', 'error']:
                if isinstance(value, (int, float)):
                    text += f"📌 <b>{key.replace('_', ' ').title()}:</b> {value:,}\n"
                elif isinstance(value, str):
                    # Try to convert string numbers
                    try:
                        if '.' in value:
                            num_val = self._safe_float(value)
                            text += f"📌 <b>{key.replace('_', ' ').title()}:</b> {num_val:,.2f}\n"
                        else:
                            num_val = self._safe_int(value)
                            text += f"📌 <b>{key.replace('_', ' ').title()}:</b> {num_val:,}\n"
                    except:
                        text += f"📌 <b>{key.replace('_', ' ').title()}:</b> {value}\n"
        
        return text
    
    def format_validators(self, validators: Dict, limit: int = 5) -> str:
        """Formats validators statistics for sending to Telegram"""
        if 'error' in validators:
            return f"❌ Error getting validators: {validators['error']}"
        
        text = "🔐 <b>Validators Statistics</b>\n\n"
        
        # Get total count
        total_validators = 0
        if isinstance(validators, dict):
            total_validators = self._safe_int(validators.get('count', 0))
        elif isinstance(validators, list):
            total_validators = len(validators)
        
        text += f"📊 <b>Total Validators:</b> {total_validators:,}\n\n"
        
        # Calculate statistics from validators list
        validators_list = []
        if isinstance(validators, dict):
            if 'validators' in validators and isinstance(validators['validators'], list):
                validators_list = validators['validators']
            elif 'data' in validators and isinstance(validators['data'], list):
                validators_list = validators['data']
        elif isinstance(validators, list):
            validators_list = validators
        
        if validators_list:
            # Count active, recent, and inactive validators
            active_count = 0
            recent_count = 0
            inactive_count = 0
            
            for validator in validators_list:
                miss_round = self._safe_int(validator.get('miss_round', 999))
                last_active_at = validator.get('last_active_at')
                
                # Active: miss_round == 0 (no missed rounds)
                if miss_round == 0:
                    active_count += 1
                # Recent: miss_round < 10 (missed less than 10 rounds)
                elif miss_round < 10:
                    recent_count += 1
                # Inactive: miss_round >= 10
                else:
                    inactive_count += 1
            
            text += f"✅ <b>Active:</b> {active_count:,}\n"
            text += f"🔄 <b>Recent:</b> {recent_count:,}\n"
            text += f"⏸️ <b>Inactive:</b> {inactive_count:,}\n"
        else:
            text += "✅ <b>Active:</b> N/A\n"
            text += "🔄 <b>Recent:</b> N/A\n"
            text += "⏸️ <b>Inactive:</b> N/A\n"
        
        return text
    
    def format_rounds(self, rounds: Dict, limit: int = 5) -> str:
        """Formats rounds list for sending to Telegram (first 5)"""
        if 'error' in rounds:
            return f"❌ Error getting rounds: {rounds['error']}"
        
        text = "🔄 <b>Latest Rounds</b>\n\n"
        
        rounds_list = []
        if isinstance(rounds, list):
            rounds_list = rounds[:limit]
        elif isinstance(rounds, dict):
            # Try different possible keys
            if 'rounds' in rounds and isinstance(rounds['rounds'], list):
                rounds_list = rounds['rounds'][:limit]
            elif 'data' in rounds and isinstance(rounds['data'], list):
                rounds_list = rounds['data'][:limit]
            else:
                return text + "No rounds data available"
        
        for round_data in rounds_list:
            # Use round ID from data only
            round_id = round_data.get('id') or round_data.get('round_id')
            if round_id:
                text += f"<b>Round {round_id}</b>\n"
                round_id_str = str(round_id)
                if len(round_id_str) > 50:
                    round_id_str = round_id_str[:47] + "..."
                text += f"   🆔 <b>ID:</b> <code>{round_id_str}</code>\n"
            else:
                text += f"<b>Round</b>\n"
            
            # Format key fields nicely
            if 'timestamp' in round_data or 'time' in round_data:
                timestamp = round_data.get('timestamp') or round_data.get('time', 'N/A')
                text += f"   🕐 <b>Time:</b> {timestamp}\n"
            if 'transactions' in round_data or 'tx_count' in round_data:
                tx_count = self._safe_int(round_data.get('transactions') or round_data.get('tx_count', 0))
                text += f"   💸 <b>Transactions:</b> {tx_count:,}\n"
            if 'validators' in round_data or 'validator_count' in round_data:
                val_count = self._safe_int(round_data.get('validators') or round_data.get('validator_count', 0))
                text += f"   🔐 <b>Validators:</b> {val_count:,}\n"
            # Add other fields
            for key, value in round_data.items():
                if key not in ['id', 'round_id', 'timestamp', 'time', 'transactions', 'tx_count', 'validators', 'validator_count']:
                    if isinstance(value, (int, float)):
                        text += f"   • <b>{key.replace('_', ' ').title()}:</b> {value:,}\n"
                    elif isinstance(value, str) and len(str(value)) < 100:
                        text += f"   • <b>{key.replace('_', ' ').title()}:</b> {value}\n"
            text += "\n"
        
        return text
    
    def format_governance(self, governance: Dict, limit: int = 5) -> str:
        """Formats governance list for sending to Telegram (first 5)"""
        if 'error' in governance:
            return f"❌ Error getting governance: {governance['error']}"
        
        text = "🏛️ <b>Latest Governance Proposals</b>\n\n"
        
        governance_list = []
        if isinstance(governance, list):
            governance_list = governance[:limit]
        elif isinstance(governance, dict):
            # Try different possible keys
            if 'vote_requests' in governance and isinstance(governance['vote_requests'], list):
                governance_list = governance['vote_requests'][:limit]
            elif 'governance' in governance and isinstance(governance['governance'], list):
                governance_list = governance['governance'][:limit]
            elif 'data' in governance and isinstance(governance['data'], list):
                governance_list = governance['data'][:limit]
            else:
                return text + "No governance data available"
        
        for i, gov in enumerate(governance_list, 1):
            # Get round number from data if available
            round_num = gov.get('round') or gov.get('round_id') or gov.get('round_number')
            if round_num:
                text += f"<b>{round_num}</b>\n"
            else:
                text += f"<b>Proposal {i}</b>\n"
            # Format key fields nicely
            if 'id' in gov:
                gov_id = gov['id']
                if len(str(gov_id)) > 60:
                    gov_id = str(gov_id)[:57] + "..."
                text += f"   🆔 <b>ID:</b> <code>{gov_id}</code>\n"
            if 'template_id' in gov:
                template = gov['template_id']
                if len(str(template)) > 60:
                    template = str(template)[:57] + "..."
                text += f"   📄 <b>Template:</b> <code>{template}</code>\n"
            if 'dso' in gov:
                dso = gov['dso']
                if len(str(dso)) > 50:
                    dso = str(dso)[:47] + "..."
                text += f"   🏢 <b>DSO:</b> <code>{dso}</code>\n"
            if 'requester' in gov:
                text += f"   👤 <b>Requester:</b> {gov['requester']}\n"
            if 'vote_before' in gov:
                text += f"   ⏰ <b>Vote Before:</b> {gov['vote_before']}\n"
            if 'reason_url' in gov and gov['reason_url']:
                reason_url = gov['reason_url']
                if len(str(reason_url)) > 80:
                    reason_url = str(reason_url)[:77] + "..."
                text += f"   🔗 <b>Reason URL:</b> {reason_url}\n"
            text += "\n"
        
        return text
    
    def format_governance_details(self, details: Dict) -> str:
        """Formats governance details showing only essential information"""
        if not details or not isinstance(details, dict):
            return "❌ Error: Invalid response from API"
        
        if 'error' in details:
            return f"❌ Error: {details['error']}"
        
        text = "🏛️ <b>Governance Details</b>\n\n"
        
        # Show only essential fields
        if 'id' in details and details['id']:
            gov_id = str(details['id'])
            if len(gov_id) > 60:
                gov_id = gov_id[:57] + "..."
            text += f"🆔 <b>ID:</b> <code>{gov_id}</code>\n"
        
        if 'template_id' in details and details['template_id']:
            template = str(details['template_id'])
            if len(template) > 60:
                template = template[:57] + "..."
            text += f"📄 <b>Template:</b> <code>{template}</code>\n"
        
        if 'dso' in details and details['dso']:
            dso = str(details['dso'])
            if len(dso) > 50:
                dso = dso[:47] + "..."
            text += f"🏢 <b>DSO:</b> <code>{dso}</code>\n"
        
        if 'requester' in details and details['requester']:
            requester = str(details['requester'])
            if len(requester) > 50:
                requester = requester[:47] + "..."
            text += f"👤 <b>Requester:</b> <code>{requester}</code>\n"
        
        if 'vote_before' in details and details['vote_before']:
            text += f"⏰ <b>Vote Before:</b> {details['vote_before']}\n"
        
        if 'reason_url' in details and details['reason_url']:
            reason_url = str(details['reason_url'])
            if len(reason_url) > 80:
                reason_url = reason_url[:77] + "..."
            text += f"🔗 <b>Reason URL:</b> {reason_url}\n"
        
        # Add status if available
        if 'status' in details and details['status']:
            status = str(details['status'])
            status_emoji = "✅" if status.lower() in ['approved', 'passed', 'active'] else "⏳" if status.lower() in ['pending', 'voting'] else "❌"
            text += f"{status_emoji} <b>Status:</b> {status}\n"
        
        if len(text) == len("🏛️ <b>Governance Details</b>\n\n"):
            text += "No additional information available"
        
        return text
    
    def format_transaction_details(self, details: Dict) -> str:
        """Formats transaction details showing only essential information"""
        if not details or not isinstance(details, dict):
            return "❌ Error: Invalid response from API"
        
        if 'error' in details:
            return f"❌ Error: {details['error']}"
        
        text = "💸 <b>Transaction Details</b>\n\n"
        
        # Show only essential fields
        tx_id = details.get('id') or details.get('tx_id') or details.get('transaction_id')
        if tx_id:
            tx_id = str(tx_id)
            if len(tx_id) > 60:
                tx_id = tx_id[:57] + "..."
            text += f"🆔 <b>ID:</b> <code>{tx_id}</code>\n"
        
        timestamp = details.get('timestamp') or details.get('time') or details.get('created_at') or details.get('date')
        if timestamp:
            text += f"🕐 <b>Time:</b> {timestamp}\n"
        
        status = details.get('status') or details.get('state')
        if status:
            status_str = str(status)
            status_emoji = "✅" if status_str.lower() in ['success', 'completed', 'confirmed', 'successful'] else "⏳" if status_str.lower() in ['pending', 'processing', 'in_progress'] else "❌"
            text += f"{status_emoji} <b>Status:</b> {status_str}\n"
        
        # Format balance fields (only show important ones)
        important_fields = ['amount', 'value', 'balance', 'fee', 'total_amount', 'transfer_amount']
        shown_fields = {'id', 'tx_id', 'transaction_id', 'timestamp', 'time', 'created_at', 'date', 'status', 'state', 'error'}
        
        for key, value in details.items():
            if key in shown_fields or value is None:
                continue
            
            # Skip nested objects and lists
            if isinstance(value, (dict, list)):
                continue
            
            # Show balance/amount fields
            if self._is_balance_field(key) or key in important_fields:
                try:
                    formatted_value = self._format_balance(value)
                    text += f"💰 <b>{key.replace('_', ' ').title()}:</b> {formatted_value} CC\n"
                except:
                    text += f"💰 <b>{key.replace('_', ' ').title()}:</b> {value}\n"
            elif isinstance(value, (int, float)):
                text += f"📊 <b>{key.replace('_', ' ').title()}:</b> {value:,}\n"
            elif isinstance(value, str) and len(str(value)) < 80:
                text += f"📌 <b>{key.replace('_', ' ').title()}:</b> {value}\n"
        
        if len(text) == len("💸 <b>Transaction Details</b>\n\n"):
            text += "No additional information available"
        
        return text
    
    def format_party_info(self, info: Dict) -> str:
        """Formats party information showing only essential information"""
        if not info or not isinstance(info, dict):
            return "❌ Error: Invalid response from API"
        
        if 'error' in info:
            return f"❌ Error: {info['error']}"
        
        text = "👥 <b>Party Information</b>\n\n"
        
        # Show only essential fields
        party_id = info.get('id') or info.get('party_id') or info.get('party')
        if party_id:
            party_id = str(party_id)
            if len(party_id) > 60:
                party_id = party_id[:57] + "..."
            text += f"🆔 <b>ID:</b> <code>{party_id}</code>\n"
        
        # Get balance from total_available_coin field
        # Check multiple possible locations
        balance = None
        
        # First, check direct field
        if 'total_available_coin' in info:
            balance = info['total_available_coin']
        # Check in amulet_balance structure
        elif 'amulet_balance' in info and isinstance(info['amulet_balance'], dict):
            amulet_balance = info['amulet_balance']
            if 'balance' in amulet_balance and isinstance(amulet_balance['balance'], dict):
                balance_dict = amulet_balance['balance']
                if 'total_available_coin' in balance_dict:
                    balance = balance_dict['total_available_coin']
        # Check in balance field structure
        elif 'balance' in info and isinstance(info['balance'], dict):
            balance_dict = info['balance']
            if 'total_available_coin' in balance_dict:
                balance = balance_dict['total_available_coin']
        
        # Format and display balance with 2 decimal places
        if balance is not None:
            try:
                # Handle different types of balance values
                if isinstance(balance, str):
                    # Remove commas and whitespace
                    balance_clean = balance.replace(',', '').replace(' ', '').strip()
                    if balance_clean == '':
                        balance_float = 0.0
                    else:
                        balance_float = float(balance_clean)
                elif isinstance(balance, (int, float)):
                    balance_float = float(balance)
                else:
                    # Try to convert using _safe_float as fallback
                    balance_float = self._safe_float(balance, default=0.0)
                
                # Format with 2 decimal places
                formatted_balance = f"{balance_float:,.2f}"
                text += f"💰 <b>Balance:</b> {formatted_balance} CC\n"
            except Exception as e:
                # If conversion fails, show raw value for debugging
                text += f"💰 <b>Balance:</b> {balance} CC\n"
        else:
            # If no balance found, show 0
            text += f"💰 <b>Balance:</b> 0.00 CC\n"
        
        # Format other important fields (skip balance fields we already handled)
        important_fields = ['amount', 'stake', 'reward', 'total_amount']
        shown_fields = {'id', 'party_id', 'party', 'error', 'balance', 'total_balance', 'balances'}
        
        for key, value in info.items():
            if key in shown_fields or value is None:
                continue
            
            # Skip nested objects and lists (except we already handled balances)
            if isinstance(value, (dict, list)):
                continue
            
            # Show balance/amount fields
            if self._is_balance_field(key) or key in important_fields:
                try:
                    formatted_value = self._format_balance(value)
                    text += f"💰 <b>{key.replace('_', ' ').title()}:</b> {formatted_value} CC\n"
                except:
                    text += f"💰 <b>{key.replace('_', ' ').title()}:</b> {value}\n"
            elif isinstance(value, (int, float)):
                text += f"📊 <b>{key.replace('_', ' ').title()}:</b> {value:,}\n"
            elif isinstance(value, str) and len(str(value)) < 80:
                text += f"📌 <b>{key.replace('_', ' ').title()}:</b> {value}\n"
        
        if len(text) == len("👥 <b>Party Information</b>\n\n"):
            text += "No additional information available"
        
        return text
    
    def format_party_transactions(self, transactions: Dict, limit: int = 20) -> str:
        """Formats party transactions showing only essential information"""
        if not transactions:
            return "❌ Error: Invalid response from API"
        
        if isinstance(transactions, dict) and 'error' in transactions:
            return f"❌ Error: {transactions['error']}"
        
        text = "💸 <b>Party Transactions</b>\n\n"
        
        transactions_list = []
        pagination_info = None
        
        if isinstance(transactions, list):
            transactions_list = transactions[:limit]
        elif isinstance(transactions, dict):
            # Check for pagination info
            if 'pagination' in transactions:
                pagination_info = transactions['pagination']
            
            # Get transactions list - API returns data in 'transactions' key
            if 'transactions' in transactions and isinstance(transactions['transactions'], list):
                transactions_list = transactions['transactions'][:limit]
            elif 'data' in transactions and isinstance(transactions['data'], list):
                transactions_list = transactions['data'][:limit]
            elif 'tx' in transactions and isinstance(transactions['tx'], list):
                transactions_list = transactions['tx'][:limit]
        
        if not transactions_list:
            return text + "No transactions available"
        
        # Show pagination info if available
        if pagination_info:
            has_next = pagination_info.get('has_next', False)
            has_previous = pagination_info.get('has_previous', False)
            if has_next or has_previous:
                text += f"📄 <b>Pagination:</b> "
                if has_previous:
                    text += "◀️ Previous "
                if has_next:
                    text += "Next ▶️"
                text += "\n\n"
        
        for i, tx in enumerate(transactions_list, 1):
            if not isinstance(tx, dict):
                continue
                
            text += f"<b>{i}.</b> "
            
            # Show update_id (primary transaction identifier) or id
            tx_id = tx.get('update_id') or tx.get('id') or tx.get('tx_id') or tx.get('transaction_id')
            if tx_id:
                tx_id = str(tx_id)
                # Show first and last parts of long IDs
                if len(tx_id) > 50:
                    tx_id_short = f"{tx_id[:25]}...{tx_id[-20:]}"
                else:
                    tx_id_short = tx_id
                text += f"<code>{tx_id_short}</code>\n"
            
            # Show choice (operation name) - this is the main action
            choice = tx.get('choice')
            if choice:
                # Clean up choice name for better readability
                choice_clean = choice.replace('_', ' ').title()
                text += f"   🔹 <b>Operation:</b> {choice_clean}\n"
            
            # Show timestamp - prefer effective_at, then record_time
            timestamp = tx.get('effective_at') or tx.get('record_time') or tx.get('timestamp') or tx.get('time') or tx.get('created_at')
            if timestamp:
                timestamp_str = str(timestamp)
                # Format ISO timestamp to be more readable
                if 'T' in timestamp_str:
                    # Format: 2025-12-05T13:01:59.960736Z -> 2025-12-05 13:01:59
                    try:
                        date_part = timestamp_str.split('T')[0]
                        time_part = timestamp_str.split('T')[1].split('.')[0]
                        timestamp_str = f"{date_part} {time_part}"
                    except:
                        pass
                text += f"   🕐 <b>Time:</b> {timestamp_str}\n"
            
            # Show consuming status
            consuming = tx.get('consuming')
            if consuming is not None:
                consuming_emoji = "🔄" if consuming else "✅"
                consuming_text = "Consuming" if consuming else "Non-consuming"
                text += f"   {consuming_emoji} <b>{consuming_text}</b>\n"
            
            # Show contract_id if available (shortened)
            contract_id = tx.get('contract_id')
            if contract_id:
                contract_id_str = str(contract_id)
                if len(contract_id_str) > 50:
                    contract_id_short = f"{contract_id_str[:25]}...{contract_id_str[-20:]}"
                else:
                    contract_id_short = contract_id_str
                text += f"   📄 <b>Contract:</b> <code>{contract_id_short}</code>\n"
            
            # Show acting parties if available
            acting_parties = tx.get('acting_parties')
            if acting_parties and isinstance(acting_parties, list) and len(acting_parties) > 0:
                party = acting_parties[0]
                if len(acting_parties) == 1:
                    party_short = str(party)
                    if len(party_short) > 40:
                        party_short = f"{party_short[:20]}...{party_short[-15:]}"
                    text += f"   👤 <b>Party:</b> <code>{party_short}</code>\n"
                else:
                    text += f"   👥 <b>Parties:</b> {len(acting_parties)}\n"
            
            text += "\n"
        
        # Add explorer link
        text += f"\n🔗 <a href='{EXPLORER_URL}'>View on Explorer</a>"
        
        return text
    
    def format_party_transfers(self, transfers: Dict, limit: int = 20) -> str:
        """Formats party transfers showing only essential information"""
        if not transfers:
            return "❌ Error: Invalid response from API"
        
        if isinstance(transfers, dict) and 'error' in transfers:
            return f"❌ Error: {transfers['error']}"
        
        text = "🔄 <b>Party Transfers</b>\n\n"
        
        transfers_list = []
        pagination_info = None
        
        if isinstance(transfers, list):
            transfers_list = transfers[:limit]
        elif isinstance(transfers, dict):
            # Check for pagination info
            if 'pagination' in transfers:
                pagination_info = transfers['pagination']
            
            # Get transfers list - try multiple possible keys
            if 'transfers' in transfers and isinstance(transfers['transfers'], list):
                transfers_list = transfers['transfers'][:limit]
            elif 'data' in transfers and isinstance(transfers['data'], list):
                transfers_list = transfers['data'][:limit]
            elif 'transfer' in transfers and isinstance(transfers['transfer'], list):
                transfers_list = transfers['transfer'][:limit]
            elif 'items' in transfers and isinstance(transfers['items'], list):
                transfers_list = transfers['items'][:limit]
        
        if not transfers_list:
            # Debug: show what keys are available and their types
            if isinstance(transfers, dict):
                keys_info = []
                for key, value in list(transfers.items())[:10]:  # Show first 10 keys
                    value_type = type(value).__name__
                    if isinstance(value, list):
                        value_type += f" (len={len(value)})"
                    keys_info.append(f"{key}: {value_type}")
                debug_msg = "No transfers available.\n"
                debug_msg += f"Response structure: {', '.join(keys_info)}"
                return text + debug_msg
            return text + "No transfers available"
        
        # Show pagination info if available
        if pagination_info:
            has_next = pagination_info.get('has_next', False)
            has_previous = pagination_info.get('has_previous', False)
            if has_next or has_previous:
                text += f"📄 <b>Pagination:</b> "
                if has_previous:
                    text += "◀️ Previous "
                if has_next:
                    text += "Next ▶️"
                text += "\n\n"
        
        for i, transfer in enumerate(transfers_list, 1):
            if not isinstance(transfer, dict):
                continue
            text += f"<b>{i}. Transfer</b>\n"
            
            # Show only essential fields
            if 'id' in transfer or 'transfer_id' in transfer:
                transfer_id = str(transfer.get('id') or transfer.get('transfer_id', 'N/A'))
                if len(transfer_id) > 50:
                    transfer_id = transfer_id[:47] + "..."
                text += f"   🆔 <b>ID:</b> <code>{transfer_id}</code>\n"
            if 'timestamp' in transfer or 'time' in transfer:
                text += f"   🕐 <b>Time:</b> {transfer.get('timestamp') or transfer.get('time', 'N/A')}\n"
            if 'from' in transfer or 'from_party' in transfer:
                from_party = str(transfer.get('from') or transfer.get('from_party', 'N/A'))
                if len(from_party) > 50:
                    from_party = from_party[:47] + "..."
                text += f"   📤 <b>From:</b> <code>{from_party}</code>\n"
            if 'to' in transfer or 'to_party' in transfer:
                to_party = str(transfer.get('to') or transfer.get('to_party', 'N/A'))
                if len(to_party) > 50:
                    to_party = to_party[:47] + "..."
                text += f"   📥 <b>To:</b> <code>{to_party}</code>\n"
            
            # Format balance fields
            for key, value in transfer.items():
                if key not in ['id', 'transfer_id', 'timestamp', 'time', 'from', 'from_party', 'to', 'to_party']:
                    if self._is_balance_field(key):
                        formatted_value = self._format_balance(value)
                        text += f"   💰 <b>{key.replace('_', ' ').title()}:</b> {formatted_value} CC\n"
                    elif isinstance(value, (int, float)):
                        text += f"   📊 <b>{key.replace('_', ' ').title()}:</b> {value:,}\n"
            
            text += "\n"
        
        # Add explorer link
        text += f"\n🔗 <a href='{EXPLORER_URL}'>View on Explorer</a>"
        
        return text

