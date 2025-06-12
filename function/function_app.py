import azure.functions as func
import cashflow.cashflow
import livestockprices.livestockprices

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */10 11-19 * * 1-5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def livestockprices(myTimer: func.TimerRequest) -> None:
    livestockprices.main()

@app.timer_trigger(schedule="0 0 19 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def cashflow(myTimer: func.TimerRequest) -> None:
    cashflow.main()