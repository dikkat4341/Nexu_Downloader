#!/bin/bash
# release.sh - Otomatik release oluşturma script'i

echo "NexusDownloader Release Creator"
echo "==============================="

# Version sor
read -p "Version (örn: 1.0.0): " version

# Git kontrol
if [[ -z $(git status -s) ]]; then
    echo "✓ Working directory clean"
else
    echo "⚠ Working directory not clean!"
    git status -s
    read -p "Devam etmek istiyor musunuz? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Tag oluştur ve push et
echo "Creating tag v$version..."
git tag "v$version"
git push origin "v$version"

echo "✓ Tag v$version created and pushed"
echo "✅ Release işlemi başlatıldı!"
echo "GitHub Actions otomatik olarak EXE'yi oluşturacak ve release'a ekleyecek."
echo "Release linki: https://github.com/$(git remote get-url origin | cut -d: -f2 | sed 's/\.git//')/releases/tag/v$version"
