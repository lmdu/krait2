#!/bin/bash

version=$1
#packager=$2

wget https://github.com/goreleaser/nfpm/releases/download/v2.20.0/nfpm_2.20.0_Linux_x86_64.tar.gz
tar xzvf nfpm_2.20.0_Linux_x86_64.tar.gz
rm nfpm_2.20.0_Linux_x86_64.tar.gz

cat > krait.desktop <<EOF
[Desktop Entry]
Version=${version}
Name=Krait
Comment=a tool for finding microsatellites from genomic sequences
GenericName=Microsatellite identification
Keywords=Microsatellite;Tandem repeats;Genome
Exec=/usr/lib/Krait/Krait %f
Icon=krait.svg
Terminal=false
Type=Application
Categories=Education
StartupNotify=true
MimeType=application/x-kpf
EOF

cat > application-x-kpf.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-kpf">
    <comment>Krait Project File</comment>
    <glob pattern="*.kpf"/>
  </mime-type>
</mime-info>
EOF

cat > nfpm.yaml <<EOF
name: Krait
arch: amd64
platform: linux
version: v${version}
section: default
priority: extra
maintainer: lmdu <adullb@qq.com>
description: a tool for finding microsatellites from genomic sequences
vendor: Bioinformatics and Integrative Genomics
homepage: https://github.com/lmdu/krait
license: MIT
contents:
  - src: ./Krait
    dst: /usr/lib/Krait
  - src: ./krait.desktop
    dst: /usr/share/applications/krait.desktop
  - src: ./application-x-kpf.xml
    dst: /usr/share/mime/packages/application-x-kpf.xml
  - src: ./logo.svg
    dst: /usr/share/icons/hicolor/scalable/apps/krait.svg
  - src: ./alogo.svg
    dst: /usr/share/icons/hicolor/scalable/mimetypes/application-x-kpf.svg
rpm:
  compression: lzma
deb:
  compression: xz
EOF

# copy logo file
cp ../src/icons/logo.svg ./logo.svg
cp ../src/icons/alogo.svg ./alogo.svg

uver=$(cat /etc/issue | cut -d " " -f2 | cut -d "." -f1)

if [ "$uver" = "20" ]
then
  linux="ubuntu20.04"
else
  linux="ubuntu22.04"
fi

./nfpm pkg -t Krait-v$version-$linux.deb
tar -czvf Krait-v$version-$linux.tar.gz Krait

#build appimage
wget --no-check-certificate --quiet https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

cp krait.desktop Krait
cp logo.svg Krait/krait.svg

mkdir -p Krait/usr/share/icons/hicolor/scalable/apps
cp logo.svg Krait/usr/share/icons/hicolor/scalable/apps/krait.svg

cat > Krait/AppRun <<'EOF'
#!/bin/bash

appdir=$(dirname $0)

exec "$appdir/Krait" "$@"

EOF
chmod 755 Krait/AppRun

cat > Krait/krait.desktop <<EOF
[Desktop Entry]
Name=Krait
Comment=a tool for finding microsatellites from genomic sequences
GenericName=microsatellite identification
Keywords=Microsatellite;Tandem repeat;Genome
Exec=Krait %F
Icon=krait
Terminal=false
Type=Application
Categories=Education
MimeType=application/x-dpf
X-AppImage-Version=${version}
EOF

mkdir -p Krait/usr/share/metainfo
cat > Krait/usr/share/metainfo/krait.appdata.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
<id>com.dulab.krait</id>
<metadata_license>CC0-1.0</metadata_license>
<project_license>MIT</project_license>
<name>Krait</name>
<summary>microsatellite identification</summary>
<description>
  <p>Krait is a tool for finding microsatellites from genomic sequences</p>
</description>
<screenshots>
  <screenshot type="default">
    <caption>Krait</caption>
    <image>https://raw.githubusercontent.com/lmdu/krait/main/src/icons/logo.svg</image>
  </screenshot>
</screenshots>
<url type="homepage">https://github.com/lmdu/krait</url>
</component>
EOF

./appimagetool-x86_64.AppImage --appimage-extract-and-run Krait Krait-v$version-$linux.AppImage
rm appimagetool-x86_64.AppImage

#./nfpm pkg -t Dockey-v${version}-amd64.rpm

#if [ "$packager" = "deb" ]
#then
#  ./nfpm pkg -t Dockey-v${version}-amd64.deb
#  #tar -czvf Dockey-v${version}-ubuntu.tar.gz Dockey
#elif [ "$packager" = "rpm" ]
#then
#  ./nfpm pkg -t Dockey-v${version}-amd64.rpm
#  #tar -czvf Dockey-v${version}-centos.tar.gz Dockey
#else
#  echo $version
#fi