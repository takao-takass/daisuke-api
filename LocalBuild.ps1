$imageName = "takao0119/daisuke-api"
$currentDateTime = "latest"#Get-Date -Format "yyyyMMdd_HHmmss"
$tag = "${imageName}:${currentDateTime}"

docker build -t $tag .

docker login
docker push $tag
docker logout

Write-Host "Docker image $tag has been built and pushed to Docker Hub."