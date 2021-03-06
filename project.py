from database_template import Base, Account, Transaction, UserWallet
import sqlalchemy
import flask
import random
import string
import httplib2
import json
import sqlalchemy_utils

#Initiate Flask Server
app = flask.Flask(__name__)

#Initiate DB Engine.
engine = sqlalchemy.create_engine('postgresql:///bankapi.db')
Base.metadata.bind = engine
dbsession = sqlalchemy.orm.sessionmaker(bind=engine)
session = dbsession()

#API reset.
@app.route('/reset')
def api_reset():
    meta = Base.metadata
    for table in reversed(meta.sorted_tables):
        session.execute(table.delete())
    session.commit()
    return 'Database Reset, return to / or /accounts' + '\n'

#Root / Show all accounts.
@app.route('/')
@app.route('/accounts')
def accounts_all():
    user = session.query(UserWallet).all()
    if user:
        accounts = session.query(Account).all()
        if accounts:
            u = 'Current Wallet: ' + str(user[0].funds) + '\n'
            x = 'Your accounts are listed below:' +'\n'
            y = '\n'.join(str(a.aid) for a in accounts)
            z = '\n''To create a new account, make a POST request to /accounts/new_ac'
            zz = '\n' + 'arguments for [name] are required.' + '\n'
            return u + x + y + z + zz
        else:
            return 'There are no accounts, curl to make some' + '\n'
    else:
        newUser = UserWallet(funds=1000000)
        session.add(newUser)
        session.commit()
        return 'Welcome, your initial personal wallet balance is 1000000sat.' + \
        '\n' + 'Follow the curl guide included in the respository to manage' + \
        '\n' + 'your accounts. Have fun and rest assured, funds are safe.' + '\n'


#Create New Account.
@app.route('/accounts/new_ac', methods=['GET','POST'])
def account_new():
    if flask.request.method == 'POST':
        data = flask.request.get_json()
        if data['name']:
            aname = data['name']
            newAccount = Account(name=aname, hodlings=0)
            session.add(newAccount)
            session.commit()
            return '{} Account Successfully Created'.format(newAccount.name) + '\n'
        else:
            return 'Arguments [name, password] are required.' + '\n'
    else:
        return 'Accounts can only be created via POST requests.' + '\n'

#Create New Transaction.
@app.route('/accounts/<int:account_id>/tx/new', methods=['GET','POST'])
def tx_new(account_id):
    try:
        active_ac = session.query(Account).filter_by(aid=account_id).one()
    except:
        return 'Invalid Account ID.' + '\n'
    if flask.request.method == 'POST':
        data = flask.request.get_json()
        if data['amount']:
            tx_amount = data['amount']
            check_bal = active_ac.hodlings + tx_amount
            userwal = session.query(UserWallet).one()
            check_wal = userwal.funds - tx_amount
            if check_bal < 0:
                return 'Not enough hodlings for specified withdrawal.' + '\n'
            elif check_wal < 0:
                return 'Not enough funds for specified deposit.' + '\n'
            new_tx = Transaction(aid=account_id, amount=tx_amount)
            session.add(new_tx)
            active_ac.hodlings += tx_amount
            userwal.funds -= tx_amount
            session.commit()
            latest_tx = session.query(Transaction).order_by(Transaction.txid.desc()).first()
            latest_txid = latest_tx.txid
            return 'Tx {} succesfully created'.format(latest_txid) + '\n'
        else:
            return 'Arguments [amount,password] are required.' + '\n'
    else:
        return 'Transactions can only be created via POST requests.' + '\n'

#API Serialized Data Endpoints.
@app.route('/accounts/<int:account_id>/JSON')
def account_page(account_id):
    try:
        active_ac = session.query(Account).filter_by(aid=account_id).one()
    except:
        return 'Invalid Account ID.' + '\n'
    return flask.jsonify(Account=active_ac.serialize)

@app.route('/accounts/<int:account_id>/tx/JSON')
def tx_all(account_id):
    try:
        active_tx = session.query(Transaction).filter_by(aid=account_id).all()
    except:
        return 'Invalid Account ID.' + '\n'
    if active_tx:
        return flask.jsonify(Transaction=[tx.serialize for tx in active_tx])
    else:
        return 'No transactions to display' + '\n'

@app.route('/accounts/<int:account_id>/tx/<int:tx_id>/JSON')
def tx_page(account_id, tx_id):
    try:
        tx = session.query(Transaction).filter_by(txid=tx_id, aid=account_id).one()
    except:
        return 'One of the specified IDs is not valid.' + '\n'
    return flask.jsonify(Transaction=tx.serialize)


if __name__ == '__Main__':
    app.run()
