#!/bin/bash

version=$1
#packager=$2

cd dist

wget https://github.com/goreleaser/nfpm/releases/download/v2.44.1/nfpm_2.44.1_Linux_x86_64.tar.gz
tar xzvf nfpm_2.44.1_Linux_x86_64.tar.gz
rm nfpm_2.44.1_Linux_x86_64.tar.gz

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

sudo apt update

sudo apt install build-essential checkinstall libegl-dev zlib1g-dev libssl-dev ninja-build autoconf libx11-dev libx11-xcb-dev libfontenc-dev libice-dev libsm-dev libxau-dev libxaw7-dev libxcomposite-dev libxcursor-dev libxdamage-dev libxdmcp-dev libxext-dev libxfixes-dev libxi-dev libxinerama-dev libxkbfile-dev libxmu-dev libxmuu-dev libxpm-dev libxrandr-dev libxrender-dev libxres-dev libxss-dev libxt-dev libxtst-dev libxv-dev libxvmc-dev libxxf86vm-dev xtrans-dev libxcb-render0-dev libxcb-render-util0-dev libxcb-xkb-dev libxcb-icccm4-dev libxcb-image0-dev libxcb-keysyms1-dev libxcb-randr0-dev libxcb-shape0-dev libglu1-mesa-dev libxcb-sync-dev libxcb-xfixes0-dev libxcb-xinerama0 libxcb-xinerama0-dev xkb-data libxcb-dri3-dev uuid-dev libxcb-util-dev libxkbcommon-x11-dev libxcb-cursor-dev libxcb-glx0-dev libxcb-dri2-0-dev libxcb-present-dev libxcb-composite0-dev libxcb-ewmh-dev libxcb-res0-dev pkg-config flex bison libfreetype-dev patchelf jq libnsl-dev -y
snap install cmake --classic --channel=3.28/stable

sudo add-apt-repository ppa:ubuntu-toolchain-r/test -y
sudo apt install -y g++-13 gcc-13
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 13
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 13
sudo update-alternatives --set gcc /usr/bin/gcc-13
sudo update-alternatives --set g++ /usr/bin/g++-13

sudo apt install coreutils binutils patchelf desktop-file-utils fakeroot fuse squashfs-tools strace util-linux zsync libgdk-pixbuf2.0-dev libxcb-cursor0 libegl1-mesa libegl1-mesa-dev libgl1-mesa-dev libgl1 libgl1-mesa-glx freeglut3-dev -y
wget --no-check-certificate --quiet https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage -O $GITHUB_WORKSPACE/appimagetool
chmod +x $GITHUB_WORKSPACE/appimagetool
pip install git+https://github.com/Frederic98/appimage-builder.git
echo "$GITHUB_WORKSPACE" >> $GITHUB_PATH

cat > AppImageBuilder.yml <<EOF
version: 1

AppDir:
  path: ./AppDir
  app_info:
    id: com.dulab.krait
    name: Krait
    icon: krait-icon.svg
    version: ${version}
    exec: Krait
    exec_args: \$@
  apt:
    arch:
      - amd64
    allow_unauthenticated: true
    sources:
      - sourceline: deb http://archive.ubuntu.com/ubuntu/ jammy main restricted universe multiverse
      - sourceline: deb http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted universe multiverse
      - sourceline: deb http://security.ubuntu.com/ubuntu jammy-security main restricted universe multiverse
    include:
      - xdg-desktop-portal-kde
      - libxcb-cursor0
      - libgl1
      - libegl1
      - libdbus-1-3
      - libgtk-3-0
      - librsvg2-2
      - librsvg2-common
      - libgdk-pixbuf2.0-0
      - libgdk-pixbuf2.0-bin
      - libgdk-pixbuf2.0-common
      - shared-mime-info
      - imagemagick
      - gnome-icon-theme-symbolic
      - hicolor-icon-theme
    exclude: []
  files:
    include: []
    exclude:
      - usr/share/man
      - usr/share/doc/*/README.*
      - usr/share/doc/*/changelog.*
      - usr/share/doc/*/NEWS.*
      - usr/share/doc/*/TODO.*
      - usr/lib/x86_64-linux-gnu/libssl.so*
  runtime:
    env:
      APPDIR_LIBRARY_PATH: "\$APPDIR:\$APPDIR/runtime/compat/:\$APPDIR/usr/lib/x86_64-linux-gnu:\$APPDIR/lib/x86_64-linux-gnu:\$APPDIR/usr/lib:\$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders"
      LD_LIBRARY_PATH: "\$APPDIR:\$APPDIR/runtime/compat/:\$APPDIR/usr/lib/x86_64-linux-gnu:\$APPDIR/lib/x86_64-linux-gnu:\$APPDIR/usr/lib:\$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders"
      PYTHONPATH: "\$APPDIR"
      QT_PLUGIN_PATH: "\$APPDIR/qt/plugins"
      QT_QPA_PLATFORMTHEME: xdgdesktopportal
      QT_QPA_PLATFORM: xcb
      GDK_PIXBUF_MODULEDIR: \$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders
      GDK_PIXBUF_MODULE_FILE: \$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders.cache
    path_mappings:
      - /usr/share:\$APPDIR/usr/share
AppImage:
  arch: x86_64
  file_name: Krait-v${version}-linux-x64.AppImage
  update-information: guess
  comp: gzip

EOF

mv Krait AppDir
icon_file=../src/icons/logo.svg
icon_dir=./AppDir/usr/share/icons/hicolor
mkdir -p ${icon_dir}/{scalable,64x64,128x128,256x256}/apps
cp ${icon_file} ${icon_dir}/scalable/apps/krait-icon.svg
cp ${icon_file} ./AppDir/krait-icon.svg

sudo apt install imagemagick

for s in 64 128 256
do
  convert -size ${s}x${s} ${icon_file} ${icon_dir}/${s}x${s}/apps/krait-icon.png
done

appimage-builder --recipe AppImageBuilder.yml --skip-test
