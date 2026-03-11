from flask import Flask, render_template, request, jsonify, abort, redirect, url_for
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)

DATA_FILE = Path(__file__).parent / "WishList.json"


def load_wishlist():
    try:
        with DATA_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_wishlist(items):
    # atomic write: write to temp then replace
    tmp = DATA_FILE.with_suffix('.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=4)
    tmp.replace(DATA_FILE)


def format_date(value):
    if not value:
        return ''
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%d %b %Y")
        except Exception:
            continue
    return value


def priority_label(value):
    try:
        v = int(value)
    except Exception:
        return str(value)
    if v == 1:
        return '★★★ High'
    if v == 2:
        return '★★ Medium'
    return '★ Low'


def priority_class(value):
    try:
        v = int(value)
    except Exception:
        return 'priority-low'
    if v == 1:
        return 'priority-high'
    if v == 2:
        return 'priority-medium'
    return 'priority-low'


app.jinja_env.filters['format_date'] = format_date
app.jinja_env.filters['priority_label'] = priority_label
app.jinja_env.filters['priority_class'] = priority_class


@app.route('/')
def home():
    items = load_wishlist()
    # simple sensible default sort: priority then date_added
    try:
        items = sorted(items, key=lambda i: (i.get('priority', 99), i.get('date_added') or '' ))
    except Exception:
        pass
    return render_template('home.html', items=items)


@app.route('/api/wishlist')
def api_wishlist():
    items = load_wishlist()
    return jsonify(items)


@app.route('/add', methods=['POST'])
def add_item():
    # support form (from HTML) and JSON payloads
    data = {}
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    item_id = data.get('id') or data.get('ID')
    if not item_id:
        abort(400, 'id is required')

    # normalize fields
    item = {
        'id': item_id,
        'Description': data.get('Description', ''),
        'category': data.get('category', ''),
        'status': data.get('status', 'WishList'),
        'url': data.get('url', '') or data.get('link_url', ''),
        'link_url': data.get('link_url', '') or data.get('url', ''),
        'timeFrame': data.get('timeFrame', ''),
        'priority': int(data.get('priority')) if data.get('priority') else 3,
        'date_added': data.get('date_added') or datetime.utcnow().strftime('%Y-%m-%d')
    }

    items = load_wishlist()
    # prevent duplicate ids
    if any(i.get('id') == item['id'] for i in items):
        abort(400, 'item with this id already exists')
    items.append(item)
    save_wishlist(items)
    # redirect back to home for form submits
    return redirect(url_for('home'))


@app.route('/remove', methods=['POST'])
def remove_item():
    if request.is_json:
        data = request.get_json()
        item_id = data.get('id')
    else:
        item_id = request.form.get('id')

    if not item_id:
        abort(400, 'id is required')

    items = load_wishlist()
    new_items = [i for i in items if str(i.get('id')) != str(item_id)]
    if len(new_items) == len(items):
        abort(404, 'item not found')
    save_wishlist(new_items)
    return redirect(url_for('manage'))


@app.route('/manage')
def manage():
    items = load_wishlist()
    try:
        items = sorted(items, key=lambda i: (i.get('priority', 99), i.get('date_added') or '' ))
    except Exception:
        pass
    return render_template('manage.html', items=items)


@app.route('/edit/<item_id>')
def edit_item(item_id):
    items = load_wishlist()
    item = next((i for i in items if str(i.get('id')) == str(item_id)), None)
    if not item:
        abort(404, 'item not found')
    return render_template('edit.html', item=item)


@app.route('/update/<item_id>', methods=['POST'])
def update_item(item_id):
    data = {}
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    items = load_wishlist()
    item = next((i for i in items if str(i.get('id')) == str(item_id)), None)
    if not item:
        abort(404, 'item not found')

    # Update item fields
    item['Description'] = data.get('Description', item.get('Description', ''))
    item['category'] = data.get('category', item.get('category', ''))
    item['status'] = data.get('status', item.get('status', 'WishList'))
    item['url'] = data.get('url', '') or data.get('link_url', '') or item.get('url', '')
    item['link_url'] = data.get('link_url', '') or data.get('url', '') or item.get('link_url', '')
    item['timeFrame'] = data.get('timeFrame', item.get('timeFrame', ''))
    item['priority'] = int(data.get('priority')) if data.get('priority') else item.get('priority', 3)

    save_wishlist(items)
    return redirect(url_for('manage'))


if __name__ == '__main__':
    app.run(debug=True)
    