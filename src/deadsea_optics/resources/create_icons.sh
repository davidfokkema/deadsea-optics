# Run on macOS and `brew install icoutils``

    Create_Icons() {
        input_filepath=$1.png
        output_iconset_name=$1.iconset

        mkdir $output_iconset_name
        sips -z 16 16     $input_filepath --out "${output_iconset_name}/icon_16x16.png"
        sips -z 32 32     $input_filepath --out "${output_iconset_name}/icon_16x16@2x.png"
        sips -z 32 32     $input_filepath --out "${output_iconset_name}/icon_32x32.png"
        sips -z 64 64     $input_filepath --out "${output_iconset_name}/icon_32x32@2x.png"
        sips -z 128 128   $input_filepath --out "${output_iconset_name}/icon_128x128.png"
        sips -z 256 256   $input_filepath --out "${output_iconset_name}/icon_128x128@2x.png"
        sips -z 256 256   $input_filepath --out "${output_iconset_name}/icon_256x256.png"
        sips -z 512 512   $input_filepath --out "${output_iconset_name}/icon_256x256@2x.png"
        sips -z 512 512   $input_filepath --out "${output_iconset_name}/icon_512x512.png"

        iconutil -c icns $output_iconset_name
        rm -R $output_iconset_name
    }

    Create_Win_Icons() {
        input_filepath=$1_win.png
        output_icon_name=$1.ico
        build_dir=build_ico

        mkdir $build_dir
        sips -z 16 16     $input_filepath --out "${build_dir}/icon_16x16.png"
        sips -z 24 24     $input_filepath --out "${build_dir}/icon_24x24.png"
        sips -z 32 32     $input_filepath --out "${build_dir}/icon_32x32.png"
        sips -z 48 48     $input_filepath --out "${build_dir}/icon_48x48.png"
        sips -z 256 256   $input_filepath --out "${build_dir}/icon_256x256.png"

        icotool -c -o $output_icon_name ${build_dir}/*
        rm -R $build_dir
    }

    Create_Icons app_icon
    Create_Win_Icons app_icon