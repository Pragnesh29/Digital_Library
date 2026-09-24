from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category, Book, Article, ArticleImage, ArticleAttachment, AuditLog, Feedback, FeedbackImage
from .forms import BookUploadForm, ArticleUploadForm, FeedbackForm
from .utils import log_action
from accounts.models import CustomUser, Department, Group

def file_contains_text(file_obj, query):
    """
    Check if a given FileField/FieldFile contains the query string (case-insensitive).
    Extracts text from PDF, TXT, CSV, MD, DOCX, etc.
    """
    if not file_obj:
        return False
    query_lower = query.lower().strip()
    if not query_lower:
        return False

    try:
        file_path = file_obj.path
    except Exception:
        return False

    filename = (file_obj.name or '').lower()

    # 1. PDF Documents
    if filename.endswith('.pdf'):
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text and query_lower in text.lower():
                    return True
        except Exception:
            pass

        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text and query_lower in text.lower():
                    return True
        except Exception:
            pass

    # 2. Plain Text / Markdown / CSV / JSON / XML / Code / Log files
    elif any(filename.endswith(ext) for ext in ['.txt', '.csv', '.md', '.rtf', '.json', '.log', '.xml', '.html', '.py']):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if query_lower in content.lower():
                    return True
        except Exception:
            pass

    # 3. Word Documents (.docx)
    elif filename.endswith('.docx'):
        try:
            import docx
            doc = docx.Document(file_path)
            for p in doc.paragraphs:
                if query_lower in p.text.lower():
                    return True
        except Exception:
            pass

    return False

def pdf_contains_text(pdf_file, query):
    return file_contains_text(pdf_file, query)

def apply_visibility_filter(qs, user):
    """
    Filter queryset based on visibility restrictions.
    Superuser and Faculty can see all approved items.
    Regular users are EXCLUDED if their department or group is listed in restricted_to_departments or restricted_to_groups.
    Unauthenticated users can only see items with NO restrictions.
    """
    if not user.is_authenticated:
        return qs.filter(restricted_to_departments__isnull=True, restricted_to_groups__isnull=True)
    if getattr(user, 'role', None) in ['faculty', 'superuser'] or getattr(user, 'is_superuser', False):
        return qs
    
    # Regular authenticated users: exclude if user's department or group matches restriction
    if hasattr(user, 'department') and user.department:
        qs = qs.exclude(restricted_to_departments=user.department)
    if hasattr(user, 'group') and user.group:
        qs = qs.exclude(restricted_to_groups=user.group)
    return qs.distinct()

def home_view(request):
    query = request.GET.get('q', '').strip()
    is_deep_search = request.GET.get('deep') == 'on' or request.GET.get('deep_search') == 'on'

    search_performed = False
    matching_books = []
    matching_articles = []

    # Search is only accessible for authenticated users
    if query and request.user.is_authenticated:
        search_performed = True
        
        # Base filter: approved books & articles with visibility restrictions applied
        approved_books = apply_visibility_filter(Book.objects.filter(is_approved=True), request.user)
        approved_articles = apply_visibility_filter(Article.objects.filter(is_approved=True), request.user)

        if not is_deep_search:
            # Standard Title, Description & Category search
            matching_books = list(approved_books.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category_tag__icontains=query) |
                Q(category__name__icontains=query)
            ).distinct().order_by('-created_at'))
            matching_articles = list(approved_articles.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            ).distinct().order_by('-created_at'))
        else:
            # Deep Search: search title, description, category, uploader AND inside PDF/attachment text contents
            candidate_articles = list(approved_articles.order_by('-created_at'))
            matched_a_list = []
            query_lower = query.lower()
            for a in candidate_articles:
                cat_name = (a.get_category_name() or '').lower()
                title_text = (a.title or '').lower()
                desc_text = (a.description or '').lower()
                uploader_name = (a.uploaded_by.username or '').lower()

                if (query_lower in title_text or 
                    query_lower in desc_text or 
                    query_lower in cat_name or 
                    query_lower in uploader_name):
                    matched_a_list.append(a)
                else:
                    # Check file attachments of the article (PDFs, Word Docs, TXT, etc.)
                    att_match = False
                    for att in a.attachments.all():
                        att_fname = (att.file_name or (att.file.name if att.file else '') or '').lower()
                        if query_lower in att_fname or (att.file and file_contains_text(att.file, query)):
                            att_match = True
                            break
                    if att_match:
                        matched_a_list.append(a)
            matching_articles = matched_a_list

            # For books: check title, description, category, uploader, AND pdf text content / pdf file name
            candidate_books = list(approved_books.order_by('-created_at'))
            matched_b_list = []
            for b in candidate_books:
                cat_name = (b.get_category_name() or '').lower()
                title_text = (b.title or '').lower()
                desc_text = (b.description or '').lower()
                cat_tag = (b.category_tag or '').lower()
                uploader_name = (b.uploaded_by.username or '').lower()

                if (query_lower in title_text or 
                    query_lower in desc_text or 
                    query_lower in cat_tag or 
                    query_lower in cat_name or 
                    query_lower in uploader_name):
                    matched_b_list.append(b)
                elif b.pdf:
                    pdf_fname = (b.pdf.name or '').lower()
                    if query_lower in pdf_fname or file_contains_text(b.pdf, query):
                        matched_b_list.append(b)
            matching_books = matched_b_list

    # Fetch highlighted books and articles for the home page carousel with visibility restrictions applied
    highlighted_books = apply_visibility_filter(Book.objects.filter(is_approved=True, is_highlighted=True), request.user).order_by('-created_at')
    highlighted_articles = apply_visibility_filter(Article.objects.filter(is_approved=True, is_highlighted=True), request.user).order_by('-created_at')
    
    # Merge highlighted list for carousel
    carousel_items = []
    for b in highlighted_books:
        cat_name = b.get_category_name()
        carousel_items.append({
            'type': 'book',
            'type_label': 'Book',
            'title': b.title,
            'tag': cat_name,
            'image': b.cover_image.url if b.cover_image else None,
            'url_name': 'book_detail',
            'pk': b.pk,
            'desc': f"Category: {cat_name} | Uploaded by {b.uploaded_by.username}"
        })
    for a in highlighted_articles:
        first_img = a.images.first()
        cat_name = a.get_category_name()
        carousel_items.append({
            'type': 'article',
            'type_label': 'Article',
            'title': a.title,
            'tag': cat_name,
            'image': first_img.image.url if first_img else None,
            'url_name': 'article_detail',
            'pk': a.pk,
            'desc': a.description[:150] + "..." if len(a.description) > 150 else a.description
        })
        
    context = {
        'carousel_items': carousel_items,
        'query': query,
        'is_deep_search': is_deep_search,
        'search_performed': search_performed,
        'matching_books': matching_books,
        'matching_articles': matching_articles,
    }
    return render(request, 'library/home.html', context)

@login_required
def book_list_view(request):
    user = request.user
    
    # Access Control: Filter books so restricted departments/groups are hidden from regular users
    books = apply_visibility_filter(Book.objects.filter(is_approved=True), user).order_by('-created_at')
    
    # Fetch lists for dropdown filters
    departments = Department.objects.all()
    categories = Category.objects.filter(Q(target_type='book') | Q(target_type='both'))
    
    context = {
        'books': books,
        'departments': departments,
        'categories': categories,
    }
    return render(request, 'library/book_list.html', context)

@login_required
def book_detail_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    user = request.user
    
    # Enforce access control for details: block if user belongs to a restricted department or group
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser or book.uploaded_by == user):
        is_dept_restricted = user.department and book.restricted_to_departments.filter(pk=user.department.pk).exists()
        is_group_restricted = user.group and book.restricted_to_groups.filter(pk=user.group.pk).exists()
        
        if is_dept_restricted or is_group_restricted:
            messages.error(request, "Access Denied: This book is restricted for your department or group.")
            return redirect('book_list')
                
    context = {
        'book': book,
    }
    return render(request, 'library/book_detail.html', context)

@login_required
def book_upload_view(request):
    if request.method == 'POST':
        form = BookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.uploaded_by = request.user
            if book.category:
                book.category_tag = book.category.name
            book.is_approved = False  # Always goes to admin approval
            book.save()
            form.save_m2m() # Required to save ManyToMany restricted departments/groups
            messages.success(request, f"Book '{book.title}' uploaded successfully! It is currently pending approval by Faculty/Admin.")
            log_action(request.user, "Book Uploaded", f"Uploaded book '{book.title}' (Pending approval)")
            return redirect('user_dashboard')
        else:
            errors_detail = " | ".join([f"{field.replace('_', ' ').capitalize()}: {', '.join(errs)}" for field, errs in form.errors.items()])
            messages.error(request, f"Book upload failed! Reason: {errors_detail}")
    else:
        form = BookUploadForm()
    return render(request, 'library/book_upload.html', {'form': form})

@login_required
def article_list_view(request):
    user = request.user
    articles = apply_visibility_filter(Article.objects.filter(is_approved=True), user).order_by('-created_at')
        
    departments = Department.objects.all()
    categories = Category.objects.filter(Q(target_type='article') | Q(target_type='both'))
    context = {
        'articles': articles,
        'departments': departments,
        'categories': categories,
    }
    return render(request, 'library/article_list.html', context)

@login_required
def article_detail_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    user = request.user
    
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser or article.uploaded_by == user):
        is_dept_restricted = user.department and article.restricted_to_departments.filter(pk=user.department.pk).exists()
        is_group_restricted = user.group and article.restricted_to_groups.filter(pk=user.group.pk).exists()
        
        if is_dept_restricted or is_group_restricted:
            messages.error(request, "Access Denied: This article is restricted for your department or group.")
            return redirect('article_list')
                
    context = {
        'article': article,
    }
    return render(request, 'library/article_detail.html', context)

@login_required
def article_upload_view(request):
    if request.method == 'POST':
        form = ArticleUploadForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.uploaded_by = request.user
            article.is_approved = False
            article.save()
            form.save_m2m()
            
            # Handle multiple file uploads (photos, PDFs, Word/Text docs)
            uploaded_files = request.FILES.getlist('files') or request.FILES.getlist('attachments') or request.FILES.getlist('images')
            for f in uploaded_files:
                ArticleAttachment.objects.create(
                    article=article,
                    file=f,
                    file_name=f.name
                )
                ext = f.name.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    ArticleImage.objects.create(article=article, image=f)
                
            messages.success(request, f"Article '{article.title}' uploaded successfully! It is currently pending approval by Faculty/Admin.")
            log_action(request.user, "Article Uploaded", f"Uploaded article '{article.title}' (Pending approval)")
            return redirect('user_dashboard')
        else:
            errors_detail = " | ".join([f"{field.replace('_', ' ').capitalize()}: {', '.join(errs)}" for field, errs in form.errors.items()])
            messages.error(request, f"Article upload failed! Reason: {errors_detail}")
    else:
        form = ArticleUploadForm()
    return render(request, 'library/article_upload.html', {'form': form})

@login_required
def user_dashboard_view(request):
    # Fetch user's uploads and submitted feedback
    books = Book.objects.filter(uploaded_by=request.user).order_by('-created_at')
    articles = Article.objects.filter(uploaded_by=request.user).order_by('-created_at')
    feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'books': books,
        'articles': articles,
        'feedbacks': feedbacks,
    }
    return render(request, 'library/dashboard.html', context)

@login_required
def cancel_upload_view(request, content_type, pk):
    # Enforce request type
    if request.method == 'POST':
        if content_type == 'book':
            item = get_object_or_404(Book, pk=pk, uploaded_by=request.user)
        elif content_type == 'article':
            item = get_object_or_404(Article, pk=pk, uploaded_by=request.user)
        else:
            messages.error(request, "Invalid upload type.")
            return redirect('user_dashboard')
            
        if not item.is_approved:
            title = item.title
            item.delete()
            messages.success(request, f"Pending upload request for '{title}' has been cancelled.")
            log_action(request.user, "Upload Cancelled", f"Cancelled pending upload request for {content_type} '{title}'")
        else:
            messages.error(request, "Cannot cancel request; it has already been approved.")
            
    return redirect('user_dashboard')


def redirect_to_admin_dashboard(request, default_tab='users-tab'):
    active_tab = request.POST.get('active_tab') or request.GET.get('tab') or default_tab
    return redirect(f"/SarvatraGyanKosh/admin-dashboard/?tab={active_tab}")

@login_required
def admin_dashboard_view(request):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied: You do not have permissions to view the Admin Dashboard.")
        return redirect('home')
        
    pending_users = CustomUser.objects.filter(is_approved=False).order_by('-date_joined')
    pending_books = Book.objects.filter(is_approved=False).order_by('-created_at')
    pending_articles = Article.objects.filter(is_approved=False).order_by('-created_at')
    
    approved_books = Book.objects.filter(is_approved=True).order_by('-created_at')
    approved_articles = Article.objects.filter(is_approved=True).order_by('-created_at')
    
    is_admin = (user.role == 'superuser' or user.is_superuser)
    all_users = CustomUser.objects.all().order_by('-date_joined') if is_admin else None
    audit_logs = AuditLog.objects.all() if is_admin else None
    all_books = Book.objects.all().order_by('-created_at')
    all_articles = Article.objects.all().order_by('-created_at')
    all_categories = Category.objects.all().order_by('name')
    all_departments = Department.objects.all().order_by('name')
    all_groups = Group.objects.all().order_by('name')
    all_feedbacks = Feedback.objects.all().order_by('-created_at') if is_admin else None
    pending_feedbacks_count = Feedback.objects.filter(status='pending').count() if is_admin else 0
    
    context = {
        'pending_users': pending_users,
        'pending_books': pending_books,
        'pending_articles': pending_articles,
        'approved_books': approved_books,
        'approved_articles': approved_articles,
        'all_users': all_users,
        'all_books': all_books,
        'all_articles': all_articles,
        'all_categories': all_categories,
        'all_departments': all_departments,
        'all_groups': all_groups,
        'audit_logs': audit_logs,
        'all_feedbacks': all_feedbacks,
        'pending_feedbacks_count': pending_feedbacks_count,
    }
    return render(request, 'library/admin_dashboard.html', context)

@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.user = request.user
            fb.save()

            uploaded_images = request.FILES.getlist('images')
            for img in uploaded_images:
                FeedbackImage.objects.create(feedback=fb, image=img)

            messages.success(request, f"Feedback '{fb.subject}' submitted successfully! Our team will review your feedback shortly.")
            log_action(request.user, "Feedback Submitted", f"Submitted feedback #{fb.id}: {fb.subject}")
            return redirect('user_dashboard')
        else:
            errors_detail = " | ".join([f"{field.replace('_', ' ').capitalize()}: {', '.join(errs)}" for field, errs in form.errors.items()])
            messages.error(request, f"Feedback submission failed! Reason: {errors_detail}")
    else:
        form = FeedbackForm()
    return render(request, 'library/feedback.html', {'form': form})

@login_required
def update_feedback_status_view(request, pk):
    user = request.user
    if not (user.role == 'superuser' or user.is_superuser):
        messages.error(request, "Access Denied: Only super admins can manage feedback.")
        return redirect('home')
        
    fb = get_object_or_404(Feedback, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'resolved', 'ignored']:
            fb.status = new_status
            fb.save()
            messages.success(request, f"Feedback #{fb.id} status updated to '{fb.get_status_display()}'.")
            log_action(user, "Feedback Status Updated", f"Updated feedback #{fb.id} status to '{fb.get_status_display()}'")
    return redirect_to_admin_dashboard(request, 'feedback-tab')

@login_required
def delete_feedback_view(request, pk):
    user = request.user
    if not (user.role == 'superuser' or user.is_superuser):
        messages.error(request, "Access Denied: Only super admins can manage feedback.")
        return redirect('home')
        
    fb = get_object_or_404(Feedback, pk=pk)
    if request.method == 'POST':
        subject = fb.subject
        fb_id = fb.id
        username = fb.user.username
        fb.delete()
        
        messages.success(request, f"Feedback #{fb_id} ('{subject}') deleted successfully.")
        log_action(user, "Feedback Deleted", f"Deleted feedback #{fb_id} submitted by '{username}' (Subject: '{subject}')")
        
    return redirect_to_admin_dashboard(request, 'feedback-tab')

@login_required
def manage_departments_view(request):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied: You do not have permissions to manage departments.")
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            if name:
                dept, created = Department.objects.get_or_create(name=name)
                if created:
                    messages.success(request, f"Department '{name}' created successfully!")
                    log_action(user, "Department Created", f"Created department '{name}'")
                else:
                    messages.info(request, f"Department '{name}' already exists.")
            else:
                messages.error(request, "Department name cannot be empty.")
        elif action == 'edit':
            dept_id = request.POST.get('department_id')
            dept = get_object_or_404(Department, pk=dept_id)
            new_name = request.POST.get('name', '').strip()
            if new_name:
                if Department.objects.filter(name=new_name).exclude(pk=dept_id).exists():
                    messages.error(request, f"Department '{new_name}' already exists.")
                else:
                    old_name = dept.name
                    dept.name = new_name
                    dept.save()
                    messages.success(request, f"Department '{old_name}' updated to '{new_name}' successfully.")
                    log_action(user, "Department Updated", f"Renamed department from '{old_name}' to '{new_name}'")
            else:
                messages.error(request, "Department name cannot be empty.")
        elif action == 'delete':
            dept_id = request.POST.get('department_id')
            dept = get_object_or_404(Department, pk=dept_id)
            dept_name = dept.name
            dept.delete()
            messages.success(request, f"Department '{dept_name}' deleted successfully.")
            log_action(user, "Department Deleted", f"Deleted department '{dept_name}'")
            
    return redirect_to_admin_dashboard(request, 'departments-tab')

@login_required
def manage_groups_view(request):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied: You do not have permissions to manage groups.")
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            if name:
                grp, created = Group.objects.get_or_create(name=name)
                if created:
                    messages.success(request, f"Group '{name}' created successfully!")
                    log_action(user, "Group Created", f"Created group '{name}'")
                else:
                    messages.info(request, f"Group '{name}' already exists.")
            else:
                messages.error(request, "Group name cannot be empty.")
        elif action == 'edit':
            grp_id = request.POST.get('group_id')
            grp = get_object_or_404(Group, pk=grp_id)
            new_name = request.POST.get('name', '').strip()
            if new_name:
                if Group.objects.filter(name=new_name).exclude(pk=grp_id).exists():
                    messages.error(request, f"Group '{new_name}' already exists.")
                else:
                    old_name = grp.name
                    grp.name = new_name
                    grp.save()
                    messages.success(request, f"Group '{old_name}' updated to '{new_name}' successfully.")
                    log_action(user, "Group Updated", f"Renamed group from '{old_name}' to '{new_name}'")
            else:
                messages.error(request, "Group name cannot be empty.")
        elif action == 'delete':
            grp_id = request.POST.get('group_id')
            grp = get_object_or_404(Group, pk=grp_id)
            grp_name = grp.name
            grp.delete()
            messages.success(request, f"Group '{grp_name}' deleted successfully.")
            log_action(user, "Group Deleted", f"Deleted group '{grp_name}'")
            
    return redirect_to_admin_dashboard(request, 'groups-tab')

@login_required
def manage_categories_view(request):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied: You do not have permissions to manage categories.")
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            target_type = request.POST.get('target_type', 'both')
            if name:
                cat, created = Category.objects.get_or_create(
                    name=name,
                    defaults={'target_type': target_type}
                )
                if created:
                    messages.success(request, f"Category '{name}' created successfully!")
                    log_action(user, "Category Created", f"Created category '{name}' ({target_type})")
                else:
                    cat.target_type = target_type
                    cat.save()
                    messages.info(request, f"Category '{name}' target type updated to {target_type}.")
            else:
                messages.error(request, "Category name cannot be empty.")
        elif action == 'edit':
            cat_id = request.POST.get('category_id')
            cat = get_object_or_404(Category, pk=cat_id)
            new_name = request.POST.get('name', '').strip()
            target_type = request.POST.get('target_type', 'both')
            if new_name:
                if Category.objects.filter(name=new_name).exclude(pk=cat_id).exists():
                    messages.error(request, f"Category '{new_name}' already exists.")
                else:
                    old_name = cat.name
                    cat.name = new_name
                    cat.target_type = target_type
                    cat.save()
                    messages.success(request, f"Category '{old_name}' updated successfully.")
                    log_action(user, "Category Updated", f"Updated category '{old_name}' -> '{new_name}' ({target_type})")
            else:
                messages.error(request, "Category name cannot be empty.")
        elif action == 'delete':
            cat_id = request.POST.get('category_id')
            cat = get_object_or_404(Category, pk=cat_id)
            cat_name = cat.name
            cat.delete()
            messages.success(request, f"Category '{cat_name}' deleted successfully.")
            log_action(user, "Category Deleted", f"Deleted category '{cat_name}'")
            
    return redirect_to_admin_dashboard(request, 'categories-tab')

@login_required
def approve_user_view(request, user_id):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            target_user.is_approved = True
            target_user.save()
            messages.success(request, f"User '{target_user.username}' has been approved.")
            log_action(user, "User Approved", f"Approved user '{target_user.username}' ({target_user.get_role_display()})")
        elif action == 'reject':
            username = target_user.username
            target_user.delete()
            messages.warning(request, f"Registration request for '{username}' was rejected.")
            log_action(user, "User Registration Rejected", f"Rejected and deleted user registration request for '{username}'")
            
    return redirect_to_admin_dashboard(request, 'users-tab')

@login_required
def approve_book_view(request, book_id):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            book.is_approved = True
            book.status = 'approved'
            book.rejection_remark = ''
            book.save()
            messages.success(request, f"Book '{book.title}' has been approved.")
            log_action(user, "Book Approved", f"Approved book '{book.title}' (Uploaded by: {book.uploaded_by.username})")
        elif action == 'reject':
            remark = request.POST.get('rejection_remark', '').strip()
            book.is_approved = False
            book.status = 'rejected'
            book.rejection_remark = remark
            book.save()
            messages.warning(request, f"Book '{book.title}' upload was marked as Rejected.")
            log_action(user, "Book Upload Rejected", f"Marked book '{book.title}' as Rejected (Uploaded by: {book.uploaded_by.username}). Reason: {remark or 'No reason provided'}")
            
    return redirect_to_admin_dashboard(request, 'books-tab')

@login_required
def approve_article_view(request, article_id):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            article.is_approved = True
            article.status = 'approved'
            article.rejection_remark = ''
            article.save()
            messages.success(request, f"Article '{article.title}' has been approved.")
            log_action(user, "Article Approved", f"Approved article '{article.title}' (Uploaded by: {article.uploaded_by.username})")
        elif action == 'reject':
            remark = request.POST.get('rejection_remark', '').strip()
            article.is_approved = False
            article.status = 'rejected'
            article.rejection_remark = remark
            article.save()
            messages.warning(request, f"Article '{article.title}' upload was marked as Rejected.")
            log_action(user, "Article Upload Rejected", f"Marked article '{article.title}' as Rejected (Uploaded by: {article.uploaded_by.username}). Reason: {remark or 'No reason provided'}")
            
    return redirect_to_admin_dashboard(request, 'articles-tab')

@login_required
def user_edit_book_view(request, pk):
    book = get_object_or_404(Book, pk=pk, uploaded_by=request.user)
    if request.method == 'POST':
        form = BookUploadForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            updated_book = form.save(commit=False)
            if updated_book.category:
                updated_book.category_tag = updated_book.category.name
            updated_book.is_approved = False
            updated_book.status = 'pending'
            updated_book.save()
            form.save_m2m()
            
            messages.success(request, f"Book '{updated_book.title}' updated successfully and resubmitted for approval!")
            log_action(request.user, "Book Resubmitted", f"Updated and resubmitted book '{updated_book.title}' for approval")
            return redirect('user_dashboard')
        else:
            errors_detail = " | ".join([f"{field.replace('_', ' ').capitalize()}: {', '.join(errs)}" for field, errs in form.errors.items()])
            messages.error(request, f"Failed to update book! Reason: {errors_detail}")
    else:
        form = BookUploadForm(instance=book)
        
    return render(request, 'library/user_edit_book.html', {'form': form, 'book': book})

@login_required
def user_edit_article_view(request, pk):
    article = get_object_or_404(Article, pk=pk, uploaded_by=request.user)
    if request.method == 'POST':
        form = ArticleUploadForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            updated_article = form.save(commit=False)
            updated_article.is_approved = False
            updated_article.status = 'pending'
            updated_article.save()
            # Delete old photos & files if user requested clear/replace
            if request.POST.get('clear_existing_files') == 'on':
                updated_article.images.all().delete()
                updated_article.attachments.all().delete()
            
            uploaded_files = request.FILES.getlist('files') or request.FILES.getlist('attachments') or request.FILES.getlist('images')
            for f in uploaded_files:
                ArticleAttachment.objects.create(
                    article=updated_article,
                    file=f,
                    file_name=f.name
                )
                ext = f.name.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    ArticleImage.objects.create(article=updated_article, image=f)
                    
            messages.success(request, f"Article '{updated_article.title}' updated successfully and resubmitted for approval!")
            log_action(request.user, "Article Resubmitted", f"Updated and resubmitted article '{updated_article.title}' for approval")
            return redirect('user_dashboard')
        else:
            errors_detail = " | ".join([f"{field.replace('_', ' ').capitalize()}: {', '.join(errs)}" for field, errs in form.errors.items()])
            messages.error(request, f"Failed to update article! Reason: {errors_detail}")
    else:
        form = ArticleUploadForm(instance=article)
        
    return render(request, 'library/user_edit_article.html', {'form': form, 'article': article})

@login_required
def toggle_highlight_view(request, content_type, pk):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    if request.method == 'POST':
        if content_type == 'book':
            item = get_object_or_404(Book, pk=pk, is_approved=True)
        elif content_type == 'article':
            item = get_object_or_404(Article, pk=pk, is_approved=True)
        else:
            messages.error(request, "Invalid content type.")
            return redirect_to_admin_dashboard(request, 'highlights-tab')
            
        item.is_highlighted = not item.is_highlighted
        item.save()
        status = "highlighted on the home page" if item.is_highlighted else "removed from home page highlights"
        messages.success(request, f"'{item.title}' has been {status}.")
        log_action(user, "Content Highlight Toggled", f"Toggled highlight status for {content_type} '{item.title}' to {item.is_highlighted}")
        
    return redirect_to_admin_dashboard(request, 'highlights-tab')

@login_required
def clear_all_highlights_view(request):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    if request.method == 'POST':
        highlighted_books_count = Book.objects.filter(is_highlighted=True).count()
        highlighted_articles_count = Article.objects.filter(is_highlighted=True).count()
        total_cleared = highlighted_books_count + highlighted_articles_count

        Book.objects.filter(is_highlighted=True).update(is_highlighted=False)
        Article.objects.filter(is_highlighted=True).update(is_highlighted=False)

        if total_cleared > 0:
            messages.success(request, f"Successfully cleared highlights from {highlighted_books_count} book(s) and {highlighted_articles_count} article(s).")
            log_action(user, "All Highlights Cleared", f"Cleared highlights from {highlighted_books_count} books and {highlighted_articles_count} articles")
        else:
            messages.info(request, "There are currently no highlighted books or articles to clear.")
            
    return redirect_to_admin_dashboard(request, 'highlights-tab')

@login_required
def delete_book_view(request, book_id):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=book_id)
        title = book.title
        uploaded_by = book.uploaded_by.username
        book.delete()
        messages.success(request, f"Book '{title}' was deleted successfully.")
        log_action(user, "Book Deleted", f"Permanently deleted book '{title}' (Uploaded by: {uploaded_by})")
        
    return redirect_to_admin_dashboard(request, 'all-books-tab')

@login_required
def delete_article_view(request, article_id):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    if request.method == 'POST':
        article = get_object_or_404(Article, pk=article_id)
        title = article.title
        uploaded_by = article.uploaded_by.username
        article.delete()
        messages.success(request, f"Article '{title}' was deleted successfully.")
        log_action(user, "Article Deleted", f"Permanently deleted article '{title}' (Uploaded by: {uploaded_by})")
        
    return redirect_to_admin_dashboard(request, 'all-articles-tab')

from django.contrib.auth.forms import SetPasswordForm

@login_required
def reset_user_password_view(request, user_id):
    user = request.user
    if not (user.role == 'superuser' or user.is_superuser):
        messages.error(request, "Access Denied: Only super administrators can reset passwords.")
        return redirect('home')
        
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(target_user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Password for '{target_user.username}' has been reset successfully.")
            log_action(user, "User Password Reset", f"Reset password for user '{target_user.username}'")
            return redirect_to_admin_dashboard(request, 'all-users-tab')
        else:
            messages.error(request, "Failed to reset password. Please review errors.")
    else:
        form = SetPasswordForm(target_user)
        
    # Style form control
    for field_name, field in form.fields.items():
        field.widget.attrs['class'] = 'form-control'
        field.widget.attrs['placeholder'] = f'Enter {field.label}'
        
    return render(request, 'library/reset_user_password.html', {'form': form, 'target_user': target_user})


@login_required
def delete_user_view(request, user_id):
    user = request.user
    if not (user.role == 'superuser' or user.is_superuser):
        messages.error(request, "Access Denied: Only super administrators can delete users.")
        return redirect('home')
        
    if request.method == 'POST':
        if user.pk == user_id:
            messages.error(request, "You cannot delete your own account.")
            return redirect_to_admin_dashboard(request, 'all-users-tab')
            
        target_user = get_object_or_404(CustomUser, pk=user_id)
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User '{username}' has been deleted successfully.")
        log_action(user, "User Deleted", f"Permanently deleted user '{username}'")
        
    return redirect_to_admin_dashboard(request, 'all-users-tab')

@login_required
def edit_book_view(request, book_id):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        form = BookUploadForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            updated_book = form.save(commit=False)
            if updated_book.category:
                updated_book.category_tag = updated_book.category.name
            updated_book.save()
            form.save_m2m()
            messages.success(request, f"Book '{book.title}' updated successfully.")
            log_action(user, "Book Edited", f"Updated book '{book.title}' (Uploaded by: {book.uploaded_by.username})")
            return redirect_to_admin_dashboard(request, 'all-books-tab')
        else:
            errors_detail = " | ".join([f"{field.replace('_', ' ').capitalize()}: {', '.join(errs)}" for field, errs in form.errors.items()])
            messages.error(request, f"Failed to update book! Reason: {errors_detail}")
    else:
        form = BookUploadForm(instance=book)
        
    return render(request, 'library/edit_book.html', {'form': form, 'book': book})

@login_required
def edit_article_view(request, article_id):
    user = request.user
    if not (user.role in ['faculty', 'superuser'] or user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        form = ArticleUploadForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            
            # Delete old photos & files if user requested clear/replace
            if request.POST.get('clear_existing_files') == 'on':
                article.images.all().delete()
                article.attachments.all().delete()

            uploaded_files = request.FILES.getlist('files') or request.FILES.getlist('attachments') or request.FILES.getlist('images')
            for f in uploaded_files:
                ArticleAttachment.objects.create(
                    article=article,
                    file=f,
                    file_name=f.name
                )
                ext = f.name.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    ArticleImage.objects.create(article=article, image=f)
                
            messages.success(request, f"Article '{article.title}' updated successfully.")
            log_action(user, "Article Edited", f"Updated article '{article.title}' (Uploaded by: {article.uploaded_by.username})")
            return redirect_to_admin_dashboard(request, 'all-articles-tab')
        else:
            errors_detail = " | ".join([f"{field.replace('_', ' ').capitalize()}: {', '.join(errs)}" for field, errs in form.errors.items()])
            messages.error(request, f"Failed to update article! Reason: {errors_detail}")
    else:
        form = ArticleUploadForm(instance=article)
        
    return render(request, 'library/edit_article.html', {'form': form, 'article': article})
