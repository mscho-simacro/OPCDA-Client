
## How to intstall 32-bit python in anaconda

> set CONDA_FORCE_32BIT=1
> conda create -n your_venv_name
> activate your_venv_name
> conda install python==3.7

> pip install OpenOPC-DA
> python -m pip install pywin32


## make stand-alone executable 
### make item list / data collector
pyinstaller --onefile --hidden-import win32timezone src/1.opcda_make_item_list.py

pyinstaller --onefile --hidden-import win32timezone src/2.opcda_data_collector.py




## 32-bit python check
python -c "import sys; print(sys.maxsize > 2**32)" 
 --> if False, 32-bit
