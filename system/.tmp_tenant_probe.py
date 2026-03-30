import tkinter as tk
from database.user_service import retrive_data
from modules import Tenant_Management, Payments_Management, Lifecycle_Management, Lease_Management
import main.Maintenance_page as MaintenancePage

user_info = retrive_data('12')
print('user_info:', user_info)

root = tk.Tk()
root.withdraw()
content = tk.Frame(root)
content.pack()

modules_to_test = {
    'Profile': Tenant_Management,
    'Payments': Payments_Management,
    'Maintenance': MaintenancePage,
    'Request Lifecycle': Lifecycle_Management,
    'Lease': Lease_Management,
}

for name, module in modules_to_test.items():
    try:
        page = module.create_page(content, user_info=user_info)
        print(name, 'OK', type(page).__name__)
    except Exception as e:
        print(name, 'ERR', type(e).__name__, e)

root.destroy()
print('probe done')
