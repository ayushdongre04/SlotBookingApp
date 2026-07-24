import contextvars

# Holds the current request's correlation ID so any logger call anywhere
# in the call stack — router, service, DB layer — can include it without
# threading it through every function signature.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)