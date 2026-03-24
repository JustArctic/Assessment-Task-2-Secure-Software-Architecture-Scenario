from flask import (render_template, url_for, flash, redirect, request, abort, Blueprint)
from flask_login import current_user, login_required
from flaskblog import db
from flaskblog.models import Post, Comment
from flaskblog.posts.utils import save_post_picture
from flaskblog.posts.forms import PostForm, CommentForm

posts = Blueprint('posts', __name__)


@posts.route("/post/new/<string:category>", methods=['GET', 'POST'])
@login_required # Only logged-in users can create posts
def new_post(category):
    form = PostForm()
    if form.validate_on_submit():
        # Blog posts do not support tags
        if category == "blog":
            tags = "" 
        else:
            tags = form.tags.data
        post = Post(title=form.title.data, content=form.content.data, author=current_user, tags=form.tags.data, category=category) # Create new Post object
        if form.picture.data:
            post.image_file = save_post_picture(form.picture.data) # Save image if uploaded
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        # Redirect based on category
        if category == "blog":
            return redirect(url_for('main.blog'))
        return redirect(url_for('main.home'))
    return render_template('create_post.html', title='New Post', form=form, category=category, legend='New Post') # Render form for GET requests or failed validation


@posts.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    page = request.args.get('page', 1, type=int) # Pagination for comments
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.date_posted.desc()).paginate(page=page, per_page=3) # Fetch comments for this post, newest first
    comment_count = Comment.query.filter_by(post_id=post.id).count()
    # Handle comment submission
    if form.validate_on_submit():
        new_comment = Comment(content=form.content.data, author=current_user, post=post)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('posts.post', post_id=post.id))
    # Render post page with comments
    return render_template('post.html', title=post.title, post=post, form=form, comments=comments, comment_count=comment_count)


@posts.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required # Only logged-in users can update posts
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin: # Only the author or an admin can update the post
        abort(403)
    form = PostForm()
    # Update post fields
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.tags = form.tags.data
        # Update image if a new one is uploaded
        if form.picture.data:
            post.image_file = save_post_picture(form.picture.data)
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('posts.post', post_id=post.id))
    elif request.method == 'GET':
        # Pre-fill form with existing post data
        form.title.data = post.title
        form.content.data = post.content
        form.tags.data = post.tags
        if form.picture.data:
            form.picture.data = save_post_picture(form.picture.data)
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


@posts.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required # Only logged-in users can delete posts
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    category = post.category
    if post.author != current_user and not current_user.is_admin: # Only the author or an admin can delete the post
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    # Redirect based on category
    if category == "blog":
        return redirect(url_for('main.blog'))
    return redirect(url_for('main.home'))


@posts.route("/comment/<int:comment_id>/update", methods=['GET', 'POST'])
@login_required # Only logged-in users can delete comments
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user and not current_user.is_admin: # Only the author or an admin can delete the comment
        abort(403)
    form = CommentForm()
    if form.validate_on_submit():
        comment.content = form.content.data
        db.session.commit()
        flash("Comment updated!", "success")
        return redirect(url_for('posts.post', post_id=comment.post_id))
    # Redirect based on category
    elif request.method == 'GET':
        form.content.data = comment.content
    return render_template("update_comment.html", form=form, comment=comment)


@posts.route("/comment/<int:comment_id>/delete", methods=['POST'])
@login_required # Only logged-in users can delete comments
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user and not current_user.is_admin: # Only the author or an admin can delete the comment
        abort(403)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted!", "success")
    return redirect(url_for('posts.post', post_id=post_id))
