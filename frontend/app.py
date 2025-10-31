import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Health check endpoint
def health_check():
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

# Добавьте health check endpoint для Streamlit
if st.runtime.exists():
    if st.request.path == "/healthz":
        if health_check():
            st.write("OK")
            st.stop()
        else:
            st.status_code(503)
            st.write("Service Unavailable")
            st.stop()

st.set_page_config(page_title="Сбор крышек", page_icon="♻️", layout="wide")

# Authentication
def check_admin_password():
    return st.session_state.get('admin_authenticated', False)

def login():
    st.sidebar.title("Административная панель")
    password = st.sidebar.text_input("Пароль администратора", type="password")
    
    if st.sidebar.button("Войти"):
        # Simple password check - in production use proper authentication
        if password == "admin123":  # Change this password
            st.session_state.admin_authenticated = True
            st.sidebar.success("Успешный вход!")
            st.rerun()
        else:
            st.sidebar.error("Неверный пароль")

# Main app
def main():
    st.title("♻️ Геймификация сбора пластиковых крышек")
    st.markdown("---")
    
    # Public section - always visible
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🏆 Рейтинг участников")
        try:
            response = requests.get(f"{API_BASE_URL}/leaderboard")
            if response.status_code == 200:
                leaderboard = response.json()
                df_individual = pd.DataFrame(leaderboard)
                if not df_individual.empty:
                    df_individual['Место'] = range(1, len(df_individual) + 1)
                    df_individual = df_individual[['Место', 'full_name', 'class_name', 'cap_count']]
                    df_individual.columns = ['Место', 'ФИО', 'Класс', 'Кол-во крышек']
                    st.dataframe(df_individual, use_container_width=True)
                else:
                    st.info("Пока нет данных о сборе крышек")
            else:
                st.error("Ошибка загрузки рейтинга")
        except Exception as e:
            st.error(f"Ошибка подключения к серверу: {e}")
    
    with col2:
        st.header("🏅 Рейтинг классов")
        try:
            response = requests.get(f"{API_BASE_URL}/class-leaderboard")
            if response.status_code == 200:
                class_leaderboard = response.json()
                df_class = pd.DataFrame(class_leaderboard)
                if not df_class.empty:
                    df_class['Место'] = range(1, len(df_class) + 1)
                    df_class = df_class[['Место', 'class_name', 'total_caps']]
                    df_class.columns = ['Место', 'Класс', 'Всего крышек']
                    st.dataframe(df_class, use_container_width=True)
                else:
                    st.info("Пока нет данных по классам")
            else:
                st.error("Ошибка загрузки рейтинга классов")
        except Exception as e:
            st.error(f"Ошибка подключения к серверу: {e}")
    
    # Statistics
    st.header("📊 Статистика")
    col1, col2, col3 = st.columns(3)
    
    try:
        response = requests.get(f"{API_BASE_URL}/leaderboard")
        if response.status_code == 200:
            leaderboard = response.json()
            total_caps = sum(item['cap_count'] for item in leaderboard)
            total_participants = len(leaderboard)
            
            with col1:
                st.metric("Всего собрано крышек", total_caps)
            with col2:
                st.metric("Участников", total_participants)
            with col3:
                if total_participants > 0:
                    avg_caps = total_caps / total_participants
                    st.metric("В среднем на участника", f"{avg_caps:.1f}")
                else:
                    st.metric("В среднем на участника", 0)
        else:
            st.info("Статистика временно недоступна")
    except:
        st.info("Статистика временно недоступна")

# Admin section
def admin_section():
    st.header("👨‍💼 Административная панель")
    
    tab1, tab2, tab3 = st.tabs(["Пользователи", "Добавить пользователя", "Статистика"])
    
    with tab1:
        st.subheader("Управление пользователями")
        try:
            response = requests.get(f"{API_BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                df_users = pd.DataFrame(users)
                if not df_users.empty:
                    st.dataframe(df_users, use_container_width=True)
                    
                    # Edit/Delete users
                    for user in users:
                        with st.expander(f"Редактировать: {user['full_name']}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                new_name = st.text_input("ФИО", value=user['full_name'], key=f"name_{user['id']}")
                            with col2:
                                new_class = st.text_input("Класс", value=user['class_name'], key=f"class_{user['id']}")
                            with col3:
                                new_pin = st.text_input("PIN код", value=user['pin_code'], max_chars=4, key=f"pin_{user['id']}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Обновить", key=f"update_{user['id']}"):
                                    update_data = {
                                        "full_name": new_name,
                                        "class_name": new_class,
                                        "pin_code": new_pin
                                    }
                                    update_response = requests.put(f"{API_BASE_URL}/users/{user['id']}", json=update_data)
                                    if update_response.status_code == 200:
                                        st.success("Пользователь обновлен")
                                        st.rerun()
                                    else:
                                        st.error("Ошибка обновления")
                            with col2:
                                if st.button("Удалить", key=f"delete_{user['id']}"):
                                    delete_response = requests.delete(f"{API_BASE_URL}/users/{user['id']}")
                                    if delete_response.status_code == 200:
                                        st.success("Пользователь удален")
                                        st.rerun()
                                    else:
                                        st.error("Ошибка удаления")
                else:
                    st.info("Нет зарегистрированных пользователей")
            else:
                st.error("Ошибка загрузки пользователей")
        except Exception as e:
            st.error(f"Ошибка подключения: {e}")
    
    with tab2:
        st.subheader("Добавить нового пользователя")
        with st.form("add_user_form"):
            full_name = st.text_input("ФИО")
            class_name = st.text_input("Класс")
            pin_code = st.text_input("PIN код (4 цифры)", max_chars=4)
            
            if st.form_submit_button("Добавить пользователя"):
                if full_name and class_name and pin_code and len(pin_code) == 4:
                    user_data = {
                        "full_name": full_name,
                        "class_name": class_name,
                        "pin_code": pin_code
                    }
                    try:
                        response = requests.post(f"{API_BASE_URL}/users", json=user_data)
                        if response.status_code == 200:
                            st.success("Пользователь успешно добавлен")
                            st.rerun()
                        else:
                            st.error("Ошибка при добавлении пользователя")
                    except Exception as e:
                        st.error(f"Ошибка подключения: {e}")
                else:
                    st.error("Заполните все поля правильно")
    
    with tab3:
        st.subheader("Административная статистика")
        try:
            users_response = requests.get(f"{API_BASE_URL}/users")
            leaderboard_response = requests.get(f"{API_BASE_URL}/leaderboard")
            
            if users_response.status_code == 200 and leaderboard_response.status_code == 200:
                users = users_response.json()
                leaderboard = leaderboard_response.json()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Всего пользователей", len(users))
                    active_users = len([u for u in leaderboard if u['cap_count'] > 0])
                    st.metric("Активных сборщиков", active_users)
                
                with col2:
                    total_caps = sum(item['cap_count'] for item in leaderboard)
                    st.metric("Всего крышек", total_caps)
                    if users:
                        participation_rate = (active_users / len(users)) * 100
                        st.metric("Процент участия", f"{participation_rate:.1f}%")
        except Exception as e:
            st.error(f"Ошибка загрузки статистики: {e}")

if __name__ == "__main__":
    # Check authentication
    if not check_admin_password():
        login()
        main()
    else:
        if st.sidebar.button("Выйти"):
            st.session_state.admin_authenticated = False
            st.rerun()
        main()
        admin_section()