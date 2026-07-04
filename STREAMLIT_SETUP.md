# Streamlit App Setup Instructions

This guide explains how to install the required Python packages, run the GroupDNA Streamlit app, and understand the libraries used by the project.

## 1. Prerequisites

- Python 3.9 or newer
- A terminal or command prompt
- Internet access to install Python packages

## 2. Open the project folder

On Windows PowerShell or Command Prompt:

```powershell
cd d:\Projects\GroupDNA
```

## 3. Create and activate a virtual environment (recommended)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again.

## 4. Install the required packages

For the Streamlit app itself, install:

```powershell
pip install -r Streamlit_App\requirements.txt
```

If you also want the notebook-based analysis environment, install the full repository requirements:

```powershell
pip install -r requirments.txt
```

## 5. Run the Streamlit app

From the project root:

```powershell
streamlit run Streamlit_App\app.py
```

After the app starts, open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## 6. Packages and libraries required

The Streamlit app uses the following Python libraries:

- streamlit: creates the web dashboard and UI
- pandas: handles tabular data and analytics output
- plotly: builds interactive charts and visualizations
- openpyxl: allows Excel export support
- reportlab: enables PDF report generation
- wordcloud: creates word clouds from chat text
- kaleido: helps export charts as static image files

Optional notebook-related packages:

- jupyterlab: notebook development interface
- ipykernel: Python kernel for Jupyter notebooks

## 7. Common commands

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Reinstall dependencies if needed:

```powershell
pip install -r Streamlit_App\requirements.txt --upgrade
```

Stop the app:

```text
Press Ctrl + C in the terminal
```

## 8. Troubleshooting

If the app does not start:

- Make sure the virtual environment is activated
- Confirm that all packages installed successfully
- Check that you are running the command from the project root
- If a port is busy, run:

```powershell
streamlit run Streamlit_App\app.py --server.port 8502
```
