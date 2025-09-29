import streamlit as st
import requests
import json


st.title("Оценка школьных работ с помощью LLM-ассистента")

OLLAMA_API_URL = f"http://localhost:11434/api/generate"

def check_ollama_connection():
    try:
        response = requests.get(f"http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

if check_ollama_connection():
    st.success("✅ Соединение с Ollama установлено")
else:
    st.error("❌ Не удается подключиться к Ollama. Убедитесь, что Ollama запущен.")
    st.stop()

criteria_file = st.file_uploader("Загрузите файл с критериями", type=['txt'])
work_file = st.file_uploader("Загрузите работу ученика", type=['txt'])
model_name = st.text_input("Модель Ollama", "qwen3:4b-instruct-2507-q8_0")
score_max = 28

if st.button("Оценить работу") and criteria_file and work_file:
    criteria_text = str(criteria_file.read(), "utf-8")
    work_text = str(work_file.read(), "utf-8")

    prompt = f"""
    Ты — опытный учитель-эксперт. Оцени работу ученика по заданным критериям. Не снижай баллы за отсутствие изображений или фотографий в работе.

    КРИТЕРИИ ОЦЕНКИ:
    {criteria_text}

    РАБОТА УЧЕНИКА:
    {work_text}

    Проанализируй работу строго по заданным критериям. Максимальный итоговый балл за работу: {score_max} баллов.
    Сформулируй ответ в виде структурированного JSON-объекта со следующими полями:
    - "overall_score": общий балл (число)
    - "criteria_breakdown": список объектов, где каждый объект имеет поля "criterion" (название критерия), "score" (балл за критерий), "comment" (развернутый комментарий)
    - "summary": общий вывод и рекомендации по улучшению (строка)

    Ответ предоставь СТРОГО в виде валидного JSON, без каких-либо дополнительных объяснений до или после него.
    Ответ должен быть строго на русском языке
    """

    with st.spinner('Идет оценка... Это может занять несколько минут.'):
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": model_name, 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {
                   #    "num_ctx": context_size
                    }
                },
                timeout=300
            )
            
            if response.status_code != 200:
                st.error(f"Ошибка Ollama (код {response.status_code}): {response.text}")
                st.stop()
                
            result = response.json()
            
            if 'response' not in result:
                st.error("Неправильный формат ответа от Ollama")
                st.json(result)
                st.stop()

            try:
                evaluation = json.loads(result['response'])
            except json.JSONDecodeError:
                st.warning("Модель вернула ответ не в JSON формате. Показываем сырой ответ:")
                st.code(result['response'])
                st.stop()

            st.success("✅ Оценка завершена!")
            
            if 'overall_score' in evaluation:
                st.subheader(f"Общий балл: {evaluation['overall_score']}/{score_max}")
            
            if 'summary' in evaluation:
                st.write("**Резюме:**")
                st.write(evaluation['summary'])

            if 'criteria_breakdown' in evaluation:
                st.subheader("Детализация по критериям:")
                for criterion in evaluation['criteria_breakdown']:
                    st.write(f"**{criterion.get('criterion', 'Без названия')}**: {criterion.get('score', 'N/A')}")
                    st.write(f"*Комментарий*: {criterion.get('comment', 'Нет комментария')}")
                    st.divider()

        except requests.exceptions.ConnectionError:
            st.error("Не удается подключиться к Ollama. Убедитесь, что Ollama запущен.")
        except requests.exceptions.Timeout:
            st.error("Время ожидания ответа от Ollama истекло. Попробуйте еще раз.")
        except Exception as e:
            st.error(f"Произошла непредвиденная ошибка: {str(e)}")
