from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from projects.models.drafts import ProjectDraft
from projects.serializers import ProjectDraftCreateSerializer, ProjectDraftListSerializer, ProjectDraftRefineSerializer, ProjectDraftUpdateSerializer, ProjectDraftDetailsSerializer, ProjectDraftFinalizeSerializer
from projects.services.gemini_service import GeminiService
from projects.services.project_seed_service import ProjectCreationError, ProjectSeederService


class ProjectDraftViewSet(viewsets.ModelViewSet):
    queryset = ProjectDraft.objects.all()
    serializer_class = ProjectDraftCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
    # we make a dictionary to map actions to serializers
    # we have creat, details, list, update, refine, generate serializers
        serializers_map = {
            'create': ProjectDraftCreateSerializer,
            'retrieve': ProjectDraftDetailsSerializer,
            'list': ProjectDraftListSerializer,
            'update': ProjectDraftUpdateSerializer,
            'partial_update': ProjectDraftUpdateSerializer,
            'refine': ProjectDraftRefineSerializer,
            'generate': ProjectDraftFinalizeSerializer,
        }

        return serializers_map.get(self.action, self.serializer_class)


    @action(detail=True, methods=['post'])
    def refine(self, request, pk=None):
        draft = self.get_object()
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({"error": "Prompt is required."}, status=status.HTTP_400_BAD_REQUEST)

        # leave the logic for the serializer to handle the prompt and draft
        serializer = self.get_serializer(draft, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        draft = self.get_object()
        serializer = self.get_serializer(draft, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

