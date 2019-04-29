from rest_framework import serializers


class ComposeProjectConfigSerializer(serializers.Serializer):
    compose_file_path = serializers.CharField(read_only=True)
    project_name: str = serializers.CharField(read_only=True)
    version: str = serializers.CharField(read_only=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    class Meta:
        fields = "__all__"


class LogsSerializer(serializers.Serializer):
    lines = serializers.IntegerField(read_only=True)
    logs = serializers.ListField(child=serializers.CharField(read_only=True), read_only=True)
    project_name: str = serializers.CharField(read_only=True)
    service_name: str = serializers.CharField(read_only=True)
    container_name: str = serializers.CharField(read_only=True)
    container_id: str = serializers.CharField(read_only=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    class Meta:
        fields = "__all__"


class ComposeFileSerializer(serializers.Serializer):
    path = serializers.CharField(read_only=True, required=False)
    file_content = serializers.CharField()
    project_name: str = serializers.CharField(read_only=True, required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    class Meta:
        fields = "__all__"
