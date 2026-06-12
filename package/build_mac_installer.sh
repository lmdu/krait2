#!/bin/bash

version=$1
arch=$2

brew install create-dmg
cd dist
create-dmg \
	--volname "Krait Installer" \
	--volicon "../src/icons/logo.icns" \
	--window-pos 200 120 \
	--window-size 800 400 \
	--icon-size 100 \
	--icon "Krait.app" 200 190 \
	--hide-extension "Krait.app" \
	--app-drop-link 600 185 \
	--hdiutil-quiet \
	"Krait-v${version}-macos-${arch}.dmg" \
	"Krait.app"

pkgbuild \
	--identifier dulab.big.krait \
	--component \
	Krait.app \
	Krait-Component.pkg \
	--install-location /Applications

productbuild \
	--synthesize \
	--package Krait-Component.pkg \
	Krait-distribution.xml

productbuild \
	--distribution Krait-distribution.xml \
	--package-path . \
	Krait-v${version}-macos-${arch}.pkg
