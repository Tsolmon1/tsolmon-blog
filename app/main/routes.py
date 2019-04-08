from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, PostForm, SearchForm, CompanyForm
from app.models import User, Post, Company_list
from app.translate import translate
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, author=current_user,
                    language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)

@bp.route("/company", methods=['GET'])
def company_namelist():
    """
    List all company
    """

    #loan_requests = Loan_request.query.all()
    page = request.args.get('page', 1, type=int)
    companys = Company_list.query.order_by(Company_list.id.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.company_namelist', page=companys.next_num) \
        if companys.has_next else None
    prev_url = url_for('main.company_namelist', page=companys.prev_num) \
        if companys.has_prev else None

    return render_template('company/company_namelists.html', companys=companys.items, title="companys", next_url=next_url, prev_url=prev_url)

@bp.route('/company/add', methods=['GET', 'POST'])
def add_company():
    form = CompanyForm()
    if form.validate_on_submit():
        company = Company_list(names_one=form.names_one.data,
                            names_two=form.names_two.data,
                            names_three=form.names_three.data,
                            branches=form.branches.data)

        # add employee to the database
        db.session.add(company)
        db.session.commit()
        flash('You have successfully registered!')

        # redirect to the login page
        return redirect(url_for('main.company_namelist'))

    # load registration template
    return render_template('company/company_add.html', form=form, title='LoanTypeAdd')
    
@bp.route('/companys/edit/<int:id>', methods=['GET', 'POST'])


def edit_company(id):
    """
    Edit a user
    """

    add_company = False

    companys = Company_list.query.get_or_404(id)
    form = CompanyForm(obj=companys)
    if form.validate_on_submit():

        companys.names_one = form.names_one.data
        companys.names_two = form.names_two.data
        companys.names_three = form.names_three.data
        companys.branches = form.branches.data

        db.session.add(companys)
        db.session.commit()
        flash('You have successfully edited the companys.')

        # redirect to the roles page
        return redirect(url_for('main.company_namelist'))

    form.names_one.data = companys.names_one
    form.names_two.data = companys.names_two
    form.names_three.data = companys.names_three
    form.branches.data = companys.branches

    return render_template('company/company_edit.html', add_company=add_company,
                           form=form, title="Edit company")

@bp.route('/company/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_company(id):
    """
    Delete a employee from the database
    """

    companyss = Company_list.query.get_or_404(id)
    db.session.delete(companyss)
    db.session.commit()
    flash('You have successfully deleted the company.')

    # redirect to the roles page
    return redirect(url_for('main.company_namelist'))