# Baton
Baton is a Python based data transfer tool, primrily written for robotic process automation (RPA), and Azure services integration. The core ideas behind its design are `operations` and `procedures`. 

`Operations` are granular and represent a particular action with a service or website. 

`Procedures` chain operations together, and are the pieces you run to achieve some outcome. 

Procedures should be idempotent/referentially transparent: or in simpler terms, if you re-run a procedure multiple times and the data/state of the systems that procedure interacts with are unchanged, you should have the same end result as if you had only run it once. This design principle also makes it safer to re-run a procedure that may have failed part way through without creating duplicates in a database or system that later need to be corrected.

Logging is implicit. Every time you run a procedure, assuming you import the logging module or another operation that uses the logging module (most do), you will generate a new log file in `/logs`. Azure Monitor integration is very easy to set up, you just need to fill in the connection_string of the private _azure method in the logging module. It would only take minimal work to integrate this with GCP, AWS, or other cloud logging services so long as they follow the OpenTelemetry standard (frankly: even Azure does not properly follow the Open Telemetry standard and this works with Azure, though OpenTelemetry attributes are missing when you query Azure Monitor).

This is a slimmed down version of a private repository. It is missing most of the original procedures, but includes most of the original operations library. 
