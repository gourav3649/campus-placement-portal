import app.models.recruiter
import inspect
print(f"Recruiter module file: {app.models.recruiter.__file__}")
print(f"Recruiter source lines:\n{inspect.getsource(app.models.recruiter.Recruiter)}")
