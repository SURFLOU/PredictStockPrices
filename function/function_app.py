import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cashflow.main import main as cashflow_main
from livestockprices.main import main as livestockprices_main
from financialratios.main import main as financialratios_main
import azure.functions as func

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */10 11-19 * * 1-5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def livestockprices(myTimer: func.TimerRequest) -> None:
    livestockprices_main()

@app.timer_trigger(schedule="0 0 19 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def cashflow(myTimer: func.TimerRequest) -> None:
    cashflow_main()

@app.timer_trigger(schedule="0 0 19 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def financialratios(myTimer: func.TimerRequest) -> None:
    financialratios_main()   
	