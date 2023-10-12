import graphene
from graphene_django.types import DjangoObjectType
from .models import PDF as PDFModel
from django.db.models import Q
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth import authenticate, logout
from graphene import String, Mutation
import graphql_jwt
from graphql_jwt.decorators import login_required

class PDFType(DjangoObjectType):
    class Meta:
        model = PDFModel

    upvote = graphene.Int()
    downvote = graphene.Int()

    def resolve_upvote(self, info):
        return self.upvote

    def resolve_downvote(self, info):
        return self.downvote
class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile

class Query(graphene.ObjectType):
    search_pdfs = graphene.List(PDFType, query=graphene.String())
    search_pdfs_by_user = graphene.List(PDFType)
    pdf_by_id = graphene.Field(PDFType, id=graphene.Int(required=True))

    def resolve_search_pdfs(self, info, query):
        if query:
            return PDFModel.objects.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(description__icontains=query) |
                Q(institution_name__icontains=query) |
                Q(link__icontains=query)
            )
        return PDFModel.objects.all()


    @login_required
    def resolve_search_pdfs_by_user(self, info):
        user = info.context.user

        if not user.is_authenticated:
            return PDFModel.objects.none()

        if user:
            print("user pdfs are being fetched")
            return PDFModel.objects.filter(user=user)

        return PDFModel.objects.none()
    @login_required
    def resolve_pdf_by_id(self, info, id):
        try:
            return PDFModel.objects.get(pk=id)
        except PDFModel.DoesNotExist:
            return None

class SignInMutation(Mutation):
    class Arguments:
        username = String(required=True)
        password = String(required=True)

    success = graphene.Boolean()
    username = graphene.String()
    token = graphene.String()

    def mutate(self, info, username, password):
        user = authenticate(username=username, password=password)
        if user:
            token = graphql_jwt.shortcuts.get_token(user)
            return SignInMutation(success=True, username=username, token=token)

class SignOutMutation(Mutation):
    success = graphene.Boolean()

    @login_required
    def mutate(self, info):
        user = info.context.user
        logout(info.context)
        return SignOutMutation(success=True)

class SignUpMutation(Mutation):
    class Arguments:
        username = String(required=True)
        password = String(required=True)
        email = String(required=True)
        first_name = String()
        last_name = String()

    success = graphene.Boolean()

    def mutate(self, info, username, password, email, first_name=None, last_name=None):
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            return SignUpMutation(success=False)

        user = User.objects.create_user(username, email, password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        UserProfile.objects.create(user=user)

        return SignUpMutation(success=True)

class CreatePDF(graphene.Mutation):
    class Arguments:
        title = graphene.String()
        description = graphene.String()
        link = graphene.String()
        author = graphene.String()
        institution_name = graphene.String()

    pdf = graphene.Field(PDFType)

    @login_required
    def mutate(self, info, title, description, link, author, institution_name):
        user = info.context.user

        pdf = PDFModel(
            user=user,
            title=title,
            description=description,
            link=link,
            author=author,
            institution_name=institution_name,
        )
        pdf.save()
        return CreatePDF(pdf=pdf)

class UpvotePDF(graphene.Mutation):
    class Arguments:
        pdf_id = graphene.Int()

    success = graphene.Boolean()

    @login_required
    def mutate(self, info, pdf_id):
        user = info.context.user
        try:
            pdf = PDFModel.objects.get(pk=pdf_id)

            # Check if the user has already upvoted this PDF
            if user in pdf.upvotes.all():
                pdf.upvotes.remove(user)
                pdf.upvote -= 1
                pdf.save()
                return UpvotePDF(success=False)

            # Remove user's downvote if exists
            if user in pdf.downvotes.all():
                pdf.downvotes.remove(user)
                pdf.downvote -= 1

            pdf.upvotes.add(user)
            pdf.upvote += 1
            pdf.save()

            return UpvotePDF(success=True)
        except PDFModel.DoesNotExist:
            return UpvotePDF(success=False)


class DownvotePDF(graphene.Mutation):
    class Arguments:
        pdf_id = graphene.Int()

    success = graphene.Boolean()

    @login_required
    def mutate(self, info, pdf_id):
        user = info.context.user
        try:
            pdf = PDFModel.objects.get(pk=pdf_id)

            # Check if the user has already downvoted this PDF
            if user in pdf.downvotes.all():
                pdf.downvotes.remove(user)
                pdf.downvote -= 1
                pdf.save()
                return DownvotePDF(success=False)

            # Remove user's upvote if exists
            if user in pdf.upvotes.all():
                pdf.upvotes.remove(user)
                pdf.upvote -= 1

            pdf.downvotes.add(user)
            pdf.downvote += 1
            pdf.save()

            return DownvotePDF(success=True)
        except PDFModel.DoesNotExist:
            return DownvotePDF(success=False)


class DeletePDF(graphene.Mutation):
    class Arguments:
        pdf_id = graphene.Int()

    success = graphene.Boolean()

    @login_required
    def mutate(self, info, pdf_id):
        user = info.context.user
        try:
            pdf = PDFModel.objects.get(pk=pdf_id)

            # Check if the user has permission to delete this PDF
            if pdf.user == user:
                pdf.delete()
                return DeletePDF(success=True)
            else:
                return DeletePDF(success=False)
        except PDFModel.DoesNotExist:
            return DeletePDF(success=False)


class EditPDF(graphene.Mutation):
    class Arguments:
        pdf_id = graphene.Int(required=True)
        title = graphene.String()
        description = graphene.String()
        link = graphene.String()
        author = graphene.String()
        institution_name = graphene.String()

    pdf = graphene.Field(PDFType)

    @login_required
    def mutate(self, info, pdf_id, title=None, description=None, link=None, author=None, institution_name=None):
        user = info.context.user

        try:
            pdf = PDFModel.objects.get(pk=pdf_id)

            # Check if the user has permission to edit this PDF
            if pdf.user != user:
                return EditPDF(pdf=None)

            if title:
                pdf.title = title
            if description:
                pdf.description = description
            if link:
                pdf.link = link
            if author:
                pdf.author = author
            if institution_name:
                pdf.institution_name = institution_name

            pdf.save()

            return EditPDF(pdf=pdf)
        except PDFModel.DoesNotExist:
            return EditPDF(pdf=None)





class Mutation(graphene.ObjectType):
    obtain_jwt_token = graphql_jwt.ObtainJSONWebToken.Field()
    refresh_jwt_token = graphql_jwt.Refresh.Field()
    verify_jwt_token = graphql_jwt.Verify.Field()
    signin = SignInMutation.Field()
    signout = SignOutMutation.Field()
    signup = SignUpMutation.Field()
    create_pdf = CreatePDF.Field()
    upvote_pdf = UpvotePDF.Field()
    downvote_pdf = DownvotePDF.Field()
    delete_pdf = DeletePDF.Field()
    edit_pdf = EditPDF.Field()

schema = graphene.Schema(query=Query, mutation=Mutation, types=[UserProfileType, PDFType])
