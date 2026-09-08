from config import *

HOSTPORT = 3251 # webserver port
CONFIGFILEPATH = "./config/pypassman.conf"  # calling for the configfile that holds all the db information
login_manager = LoginManager() #login, registration handler

db = SQLAlchemy()  # database connection handler

def create_app():
        #when the create_app function is called, establish the name, and the templates folder that contains the templates that should be used by the application.
    pypassmanapp = Flask(__name__,template_folder = './resources/www/', static_folder = './resources')

    pypassmanapp.config['SECRET_KEY']=config.ConfigFile(CONFIGFILEPATH).get_crypt_phrase()
        #db initial connection string, config in running app
    pypassmanapp.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{config.ConfigFile(CONFIGFILEPATH).get_dbuser()}:{config.ConfigFile(CONFIGFILEPATH).get_dbpass()}@{config.ConfigFile(CONFIGFILEPATH).get_host()}/pypassman_db'
    pypassmanapp.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        #initializing db connection and login_manager to with the application's details
    MasterAccess.db.init_app(pypassmanapp)

    login_manager.init_app(pypassmanapp)
    login_manager.login_view = "logon"

    print(config.ConfigFile(CONFIGFILEPATH).get_server("CENTRAL",True))
    with pypassmanapp.app_context():
        MasterAccess.db.create_all()
        #route : URL Route Registrations, Decorate a view function to register it with the given URL rule and options. Calls add_url_rule(),
        #which has more details about the implementation. Following def index():
    @pypassmanapp.route("/")
    def index():
        return render_template("index.html")
    @pypassmanapp.route("/about")
    def about():
        try:
            print(current_user.name)
            print(current_user.email_address)
        except Exception as e:
            pass
        return render_template("about.html")
    @pypassmanapp.route("/logon", methods=["GET","POST"])
    def logon():
        errors = []
        if request.method == "POST":
            username = (request.form["email"] or "").strip()
            password = (request.form["password"] or "")

            if not username:
                errors.append("Username must be provided.")
            elif not password:
                errors.append("Password must be provided.")

            if not errors:
                try:

                    print("before")
                    user = MasterAccess.User.query.filter_by(email_address=username).first()
                    print("after")
                    if not user or not check_password_hash(user.pswd, password):
                        errors.append(f"Login Failed")
                    else:
                        try:
                            login_user(user, remember=config.ConfigFile(CONFIGFILEPATH).get_server("CENTRAL",True))
                            return redirect(url_for("dashboard"))
                        except Exception as e:
                            print(e)
                            # user = MasterAccess.User.query.filter_by(email_address=username).first()
                            # print(user,user.pswd)
                            errors.append(f"LOGIN Failed with: {e}")
                            return render_template("logon.html", errors=errors), 500
                except Exception as e:
                    print(e)
                    # user = MasterAccess.User.query.filter_by(email_address=username).first()
                    # print(user.pswd)
                    errors.append(f"LOGIN Failed with: {e}")
                    return render_template("logon.html", errors=errors), 500
            if errors:
                return render_template("logon.html", errors=errors)

        return render_template("logon.html")

    @login_manager.user_loader
    def load_user(user_id):
        return MasterAccess.db.session.get(MasterAccess.User, int(user_id))

    @pypassmanapp.route("/delete_entry/<int:eid>", methods=["POST"])
    @login_required
    def delete_entry(eid):
            #Only retrieve an entry belonging to the logged-in user
        entry = MasterAccess.PassmanEntry.query.filter_by(eid=eid,uid=current_user.id).first_or_404()
        try:
            db.session.delete(entry)
            db.session.commit()
            flash("Password entry deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting entry: {e}")
            flash("Unable to delete password entry.", "error")
        return redirect(url_for("dashboard"))

    @pypassmanapp.route("/edit_entry/<int:eid>", methods=["GET", "POST"])
    @login_required
    def edit_entry(eid):

        #Only retrieve an entry belonging to the logged-in user
        #entry = MasterAccess.PassmanEntry.query.filter_by(eid=eid,uid=current_user.id).first_or_404()
        entry = MasterAccess.get_passman_entry(current_user.id,eid)

        if entry is None:
            return "Entry not found.", 404
        if request.method == "POST":
            entry_name = request.form.get("entry_name", "").strip()
            entry_username = request.form.get("entry_username", "").strip()
            entry_password = request.form.get("entry_password", "")
            site_url = request.form.get("site_url", "").strip()

            # Validate required fields
            if not entry_name:
                flash("Entry name is required.", "error")
                return render_template("edit_entry.html",entry=entry)

            if not entry_username:
                flash("Username is required.", "error")
                return render_template("edit_entry.html",entry=entry)

            if not entry_password:
                flash("Password is required.", "error")
                return render_template("edit_entry.html",entry=entry)

                # Update fields
            # entry.entry_name = entry_name
            # entry.entry_username = entry_username
            # entry.entry_password = entry_password
            # entry.site_url = site_url if site_url else None
            # entry.last_modified = datetime.utcnow()

            try:
                # db.session.commit()
                MasterAccess.update_passman_entry(
                    uid=current_user.id,
                    eid=eid,
                    entry_name=entry_name,
                    entry_username=entry_username,
                    entry_password=entry_password,
                    site_url=site_url if site_url else None
                )
                flash("Password entry updated successfully.", "success")
                return redirect(url_for("dashboard"))

            except Exception as e:
                db.session.rollback()

                print(f"Error updating entry: {e}")

                flash("Unable to update password entry.", "error")

                return render_template("edit_entry.html",entry=entry), 500

        return render_template(
            "edit_entry.html",
            entry=entry
        )

    @pypassmanapp.route("/create_entry", methods=["GET", "POST"])
    @login_required
    def create_entry():
        if request.method == "POST":
            entry_name = request.form.get("entry_name", "").strip()
            entry_username = request.form.get("entry_username", "").strip()
            entry_password = request.form.get("entry_password", "")
            site_url = request.form.get("site_url", "").strip()
                # Validate required fields
            if not entry_name:
                flash("Entry name is required.", "error")
                return render_template("create_entry.html")
            if not entry_username:
                flash("Username is required.", "error")
                return render_template("create_entry.html")
            if not entry_password:
                flash("Password is required.", "error")
                return render_template("create_entry.html")

                # Create the entry
            try:
                print("Creating entry before")
                # entry = MasterAccess.PassmanEntry()
                # entry.uid = current_user.id
                # entry.entry_name=entry_name
                # entry.entry_username=entry_username
                # entry.entry_password=entry_password
                # entry.site_url=site_url if site_url else None
                # entry.create_date=datetime.utcnow(),
                # entry.last_modified=datetime.utcnow()
                MasterAccess.create_passman_entry(
                    uid=current_user.id,
                    entry_name=entry_name,
                    entry_username=entry_username,
                    entry_password=entry_password,
                    site_url=site_url if site_url else None
                )
                print("Creating entry after")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating entry: {e}")
                flash(f"Unable to create password entry with: {e}", "error")
                return render_template("create_entry.html"), 500

            try:
                print("DB session before")
                # MasterAccess.db.session.add(entry)
                # MasterAccess.db.session.commit()
                flash("Password entry created successfully.", "success")
                print("DB session after")
                return redirect(url_for("dashboard")), 500

            except Exception as e:
                db.session.rollback()
                print(f"Error creating entry: {e}")
                flash("Unable to create password entry.", "error")
                return render_template("create_entry.html")

        return render_template("create_entry.html")


    @pypassmanapp.route("/register", methods=["GET","POST"])
    def register():
        errors = []
        if request.method == "POST":
            username = (request.form["username"] or "").strip()
            password = (request.form["password"] or "")
            confirm = (request.form["confirm_password"] or "")
            email = request.form.get("email", "").strip().lower()
            cryptkey = (request.form["cryptkey"] or "").strip()

            # -------------------------
            # Checks for Duplicate user, Validate cryptkey, email, password, username, Confirm password
            # -------------------------
            if not (4 <= len(username) <= 94):
                errors.append("Username must be between 4 and 94 characters long.")
            elif not re.match("^[A-Za-z0-9_.-]+$", username):
                errors.append("Username must contain only letters, numbers, dots and dashes.")
            elif not re.match("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
                errors.append("Invalid Password")
            elif not re.match("^[\w\-\.]+@([\w-]+\.)+[\w-]{2,}$",email):
                errors.append("Invalid Email")
            elif not password == confirm:
                errors.append("Passwords must match.")
            elif not cryptkey:
                errors.append("Cryptkey Phrase cannot be empty.")
            elif not errors:
                # Check username
                existing_username = MasterAccess.User.query.filter_by(name=username).first()
                if existing_username:errors.append("Username already exists.")
                # Check email
                existing_email = MasterAccess.User.query.filter_by(email_address=email).first()
                if existing_email:errors.append("Email address is already registered.")
            # Create user AND redirect to Dashboard
            if not errors:
                try:
                    pwd = generate_password_hash(password)
                    user = MasterAccess.User()
                    user.name = username
                    user.pswd = pwd
                    user.email_address = email
                    user.cryptkey = cryptkey
                    MasterAccess.db.session.add(user)
                    MasterAccess.db.session.commit()
                    return redirect(url_for("dashboard"))
                except Exception as e:
                    MasterAccess.db.session.rollback()
                        # Handle database duplicate constraint
                    error_message = str(e).lower()
                    if "duplicate" in error_message or "unique constraint" in error_message or "1062" in error_message:
                        errors.append("An account with that username or email already exists.")
                    else:
                        errors.append(f"Registration Failed with: {e}")
                    return render_template("register.html",errors=errors), 400
            if errors:
                return render_template("register.html", errors=errors)
        return render_template("register.html")

    @pypassmanapp.route("/dashboard")
    @login_required
    def dashboard():
        print(current_user.name)
        print(current_user.email_address)

        return render_template("dashboard.html")

    @pypassmanapp.route("/dbhealthcheck")
    @login_required
    def dbhealthcheck():
        try:
            MasterAccess.db.session.execute(text("SELECT 1"))
            return {"db": "okay"},200
        except Exception as e:
            return {"db": "encountered error", "details: ": str(e)}, 500

    @pypassmanapp.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("logon"))

    @pypassmanapp.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    return pypassmanapp

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=HOSTPORT)



