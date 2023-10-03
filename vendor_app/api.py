import frappe
from frappe import auth

@frappe.whitelist( allow_guest=True )
def register_user(email, name, password):
    login_manager = frappe.auth.LoginManager()
    login_manager.authenticate(user="Administrator", pwd="trampoline")
    login_manager.post_login()
    # Create a new user document
    new_user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": name,
        "new_password": password
    })

    # Save the user document
    new_user.insert()

    # Assign the role to the user
    frappe.get_doc("User", email).add_roles("Supplier")

    new_supplier = frappe.get_doc({
        "doctype": "Supplier",
        "user_id": email,
        "supplier_name": name,
        "email": email
    })
    new_supplier.insert()
    login_manager.logout()
    frappe.response["message"] = {
        "success": True,
        "data": new_user
    }

@frappe.whitelist( allow_guest=True )
def login(usr, pwd):
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Authentication Error!"
        }

        return

    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)
    supplier = frappe.get_list('Supplier', filters={'user_id':user.name})

    # TODO Handle error
    # if(len(supplier) == 1):
    #     frappe.response("Supplier not found", 401);
    
    frappe.response["message"] = {
        "success_key":1,
        "message":"Authentication success",
        "sid":frappe.session.sid,
        "api_key":user.api_key,
        "api_secret":api_generate,
        "username":user.username,
        "email":user.email,
        "supplier_id": supplier[0].name

    }



def generate_keys(user):
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)

    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key

    user_details.api_secret = api_secret
    user_details.save()

    return api_secret