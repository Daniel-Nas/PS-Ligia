import streamlit as st
import pandas as pd
import joblib
import numpy as np
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="Previsão de Qualidade do Sono", layout="wide")

def create_gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Score de Qualidade do Sono", 'font': {'size': 24}},
        number={'font': {'size': 50, 'color': "white"}},  
        gauge={
            'axis': {
                'range': [0, 10], 
                'tickwidth': 1, 
                'tickcolor': "darkblue", 
                'dtick': 1,  
                'tickfont': {'size': 18, 'color': "white"} 
            },
            'bar': {'color': "white"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 4.5], 'color': 'darkblue'},
                {'range': [4.5, 7.0], 'color': 'blue'},
                {'range': [7.0, 10], 'color': 'lightblue'}
            ],
        }
    ))
    fig.update_layout(autosize=True, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# Função para carregar os artefatos
@st.cache_resource
def load_models():
    model = joblib.load('Modelo_Final/modelo_XGBoost.joblib')
    scaler = joblib.load('Modelo_Final/scaler.joblib')
    ord_encoder = joblib.load('Modelo_Final/ord_encoder.joblib')
    ohe_encoder = joblib.load('Modelo_Final/ohe_encoder.joblib')
    model_columns = joblib.load('Modelo_Final/colunas.joblib')
    return model, scaler, ord_encoder, ohe_encoder, model_columns

model, scaler, ord_encoder, ohe_encoder, model_columns = load_models()

st.title("🌙 Dashboard de Análise e Previsão de Qualidade de Sono")
st.markdown("Insira seus dados abaixo para prever o score de qualidade do seu sono.")
st.divider()

# Seção 1: perfil
with st.expander("👤 Perfil", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        age = st.number_input("Idade", min_value=18, max_value=100, value=25)
        occupation = st.selectbox("Ocupação", [
            "Software Engineer", "Doctor", "Sales Representative", "Teacher", 
            "Nurse", "Engineer", "Accountant", "Scientist", "Lawyer", "Salesperson", "Manager"
        ])
    with c2:
        gender = st.selectbox("Gênero", ["Male", "Female"])

# Seção 2: atividade e saúde
with st.expander("🏃 Atividade e Saúde", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        physical_activity = st.slider("Nível de Atividade Física (min/dia)", 0, 120, 30)
        daily_steps = st.number_input("Passos Diários", min_value=0, max_value=20000, value=5000)
    with c2:
        bmi_category = st.selectbox("Categoria de IMC", ["Normal", "Overweight", "Obese"])
        heart_rate = st.number_input("Frequência Cardíaca (bpm)", min_value=40, max_value=120, value=70)

# Seção 3: sono
with st.expander("💤 Detalhes do Sono", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        sleep_duration = st.number_input("Duração do Sono (horas)", min_value=0.0, max_value=12.0, value=7.0, step=0.1)
        stress_level = st.slider("Nível de Estresse (1-10)", 1, 10, 5)
    with c2:
        bp_category = st.selectbox("Categoria de Pressão Arterial", [
            "Normal", "Prehypertension", "Hypertension Stage 1", "Hypertension Stage 2", "Hypertensive Crisis"
        ])
        sleep_disorder = st.selectbox("Distúrbio de Sono", ["Normal", "Insomnia", "Sleep Apnea"])

# Botão de Previsão 
st.markdown("<br>", unsafe_allow_html=True) 
if st.button("Calcular Qualidade do Sono", type="primary", use_container_width=True):
    
    # DataFrame de entrada
    input_df = pd.DataFrame([{
        'Age': age,
        'Gender': gender,
        'Occupation': occupation,
        'Sleep Duration': sleep_duration,
        'Physical Activity Level': physical_activity,
        'Stress Level': stress_level,
        'BMI Category': bmi_category,
        'Heart Rate': heart_rate,
        'Daily Steps': daily_steps,
        'Sleep Disorder': sleep_disorder,
        'BP_Category': bp_category
    }])

    # Transformação das nossas variáveis ordinais (pra aparecer normal) 
    input_df[['BMI Category', 'BP_Category']] = ord_encoder.transform(input_df[['BMI Category', 'BP_Category']])
    
    # Transformação das nossas variáveis categóricas (pra aparecer normal) 
    categorical_cols = ['Gender', 'Occupation', 'Sleep Disorder']
    encoded_cats = ohe_encoder.transform(input_df[categorical_cols])
    encoded_df = pd.DataFrame(encoded_cats, columns=ohe_encoder.get_feature_names_out(categorical_cols))

    # Transformação das nossas variáveis numéricas (pra aparecer normal) 
    numerical_cols = ['Age', 'Sleep Duration', 'Physical Activity Level', 'Stress Level', 'Heart Rate', 'Daily Steps']
    input_df[numerical_cols] = scaler.transform(input_df[numerical_cols])

    # Concatenar e alinhar colunas
    final_df = pd.concat([input_df[numerical_cols + ['BMI Category', 'BP_Category']], encoded_df], axis=1)

    final_df = final_df.reindex(columns=model_columns, fill_value=0)

    # Predição
    prediction = model.predict(final_df)[0]
    prediction = float(np.clip(prediction, 0, 10))

    # Exibe do Resultado
    st.divider()
    
    res_col1, res_col2 = st.columns([1, 2]) 

    with res_col1:
        fig_gauge = create_gauge_chart(prediction)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with res_col2:
        st.subheader("Análise do Resultado")
        
        if prediction >= 7.0:
            st.success(f"### Excelente! 🌟\nSua nota foi **{prediction:.2f}**. Seu sono está num nível ótimo.")
        elif prediction >= 4.5:
            st.warning(f"### Moderado ⚠️\nSua nota foi **{prediction:.2f}**. Existem pontos de atenção na sua rotina.")
        else:
            st.error(f"### Baixo 🚨\nSua nota foi **{prediction:.2f}**. Recomendamos procurar um especialista.")

        st.info(f"**Resumo:** Você dorme **{sleep_duration}h** e reportou estresse nível **{stress_level}/10**.")