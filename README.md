# 🎯 Fidelidade — Sistema de Gestão de Clientes Fidelizados

**Fidelidade** é um sistema web desenvolvido para empresas que desejam implementar um programa de fidelidade simples, eficiente e digital. Com ele, é possível cadastrar clientes, registrar interações, acompanhar pontos acumulados e facilitar a gestão de recompensas.

---

## 🚀 Funcionalidades

- ✅ Cadastro de clientes com dados pessoais
- 🎁 Acúmulo de pontos por visitas, compras ou serviços
- 📊 Painel com histórico e saldo de pontos por cliente
- 🔐 Login de administrador e controle de acesso
- 📅 Registro de atividades e interações
- 📤 Interface simples e responsiva

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**
- **Django 4.x**
- **SQLite3** (desenvolvimento local)
- **HTML5, CSS3, JavaScript**
- **Bootstrap** (interface)

---

## 📦 Como rodar o projeto localmente

### 1. Clone o repositório

```bash
git clone https://github.com/celsoleite38/fidelidade.git
cd fidelidade
# Crie e ative um ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt

# rode as migrações par criar o bd.
python manage.py migrate
python manage.py runserver


# Aplique as migrações
python manage.py migrate

# Execute o servidor de desenvolvimento
python manage.py runserver
