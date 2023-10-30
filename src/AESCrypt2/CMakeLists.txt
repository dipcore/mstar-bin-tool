cmake_minimum_required(VERSION 3.9)

set( CMAKE_OSX_ARCHITECTURES i386 CACHE STRING "" )

project( aescrypt2 )

set( HEADER_FILES
   aes.h
   sha256.h )

set( SOURCE_FILES
   aes.c
   sha256.c )

add_executable( aescrypt2 aescrypt2.c ${SOURCE_FILES} )
