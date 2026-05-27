# Local Two-Repo Test Steps

Use these steps to test the Streamlit frontend from a clean folder while keeping the frontend repo separate from the backend/data repo.

## 1. Create a clean test folder

```bash
mkdir -p ~/Desktop/panasillies-local-test
cd ~/Desktop/panasillies-local-test
```

## 2. Clone the frontend repo

```bash
git clone https://github.com/Joy0727/INF191-Panasillies-streamlit-demo.git
```

## 3. Clone the backend/data repo

```bash
git clone https://github.com/anverchou/INF191-Panasillies.git
```

After cloning, the folder should look like this:

```text
panasillies-local-test/
  INF191-Panasillies-streamlit-demo/
  INF191-Panasillies/
```

## 4. Enter the frontend repo

```bash
cd INF191-Panasillies-streamlit-demo
```

## 5. Install dependencies

```bash
pip install -r requirements.txt
```

## 6. Run the Streamlit frontend with the backend data path

```bash
PANASILLIES_DATA_DIR=../INF191-Panasillies python3 run.py
```

## 7. Open the app

Open the URL shown in the terminal, usually:

```text
http://localhost:8501
```

If port 8501 is busy, Streamlit may show a different URL such as:

```text
http://localhost:8502
```

## 8. Login

```text
Email: panasillies.user@panasonic.aero
Password: password
```

## Expected behavior

- The Dashboard should load real backend output data from the cloned `INF191-Panasillies` folder.
- Creating a new campaign should only store demo state in the browser.
- No CSV, model, or backend files should be modified.
