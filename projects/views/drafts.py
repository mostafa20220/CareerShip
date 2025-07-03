from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from projects.models.drafts import ProjectDraft
from projects.serializers import ProjectDraftSerializer
from projects.services.gemini_service import GeminiService
from projects.services.project_seed_service import ProjectCreationError, ProjectSeederService


class ProjectDraftViewSet(viewsets.ModelViewSet):
    queryset = ProjectDraft.objects.all()
    serializer_class = ProjectDraftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def refine(self, request, pk=None):
        draft = self.get_object()
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({"error": "Prompt is required."}, status=status.HTTP_400_BAD_REQUEST)

        gemini_service = GeminiService()
        # Assuming the service can take conversation history for refinement
        # For now, we just send the new prompt
        refined_project = gemini_service.generate_project(prompt)

        draft.generated_project = refined_project
        draft.save()

        serializer = self.get_serializer(draft)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create(self, request, pk=None):
        draft = self.get_object()
        try:
            service = ProjectSeederService(draft.generated_project)
            project = service.create_project()
        except ProjectCreationError as e:
            return Response({'error': str(e)}, status=e.status_code)

        response_data = {
            'id': project.id,
            'name': project.name,
            'slug': project.slug,
            'message': 'Project created successfully.',
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

