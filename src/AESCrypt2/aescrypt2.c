/*
 *  AES-CBC-256/HMAC-SHA256 file encryption
 *
 *  Copyright (C) 2004,2005  Christophe Devine
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#ifndef WIN32
#include <sys/types.h>
#include <unistd.h>
#else
#include <windows.h>
#include <io.h>
#endif

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#include "aes.h"
#include "sha256.h"

#define MODE_ENCRYPT    0
#define MODE_DECRYPT    1

/* miscellaneous utility routines */

void do_exit( int retcode )
{
#ifdef WIN32
    int i;

    printf( "\nPress Ctrl-C to exit.\n" );
    scanf( "%d", &i );
#endif

    exit( retcode );
}

int my_fread( FILE *f, void *ptr, size_t size )
{
    if( fread( ptr, 1, size, f ) != size )
    {
        if( ferror( f ) )
        {
            fprintf( stderr, "fread(%d bytes) failed\n", size );
            return( 1 );
        }

        if( feof( f ) )
        {
            fprintf( stderr, "fread(%d bytes): short file\n", size );
            return( 1 );
        }
    }

    return( 0 );
}

int my_fwrite( FILE *f, void *ptr, size_t size )
{
    if( fwrite( ptr, 1, size, f ) != size )
    {
        if( ferror( f ) )
        {
            fprintf( stderr, "fwrite(%d bytes) failed\n", size );
            return( 1 );
        }

        if( feof( f ) )
        {
            fprintf( stderr, "fwrite(%d bytes): short file\n", size );
            return( 1 );
        }
    }

    return( 0 );
}

/* program entry point */

int main( int argc, char *argv[] )
{
    char user_key[512];
    unsigned char IV[16];
    unsigned char tmp[16];
    unsigned char digest[32];
    unsigned char k_ipad[64];
    unsigned char k_opad[64];
    unsigned char buffer[1024];

    int i, n, mode, lastn;
    FILE *fkey, *fin, *fout;

#ifndef WIN32
    off_t filesize, offset;
#else
    __int64 filesize, offset;
#endif

    aes_context aes_ctx;
    sha256_context sha_ctx;

    /* check the arguments */

    if( argc != 5 )
    {
        printf( "\n  aescrypt2 <mode> <infile> <outfile> <key file ||"
                " key string>\n\n  mode 0 = encrypt, 1 = decrypt\n\n" );

#ifdef WIN32
        printf( "\n" );

        printf( "  mode    -> " );
        argv[1] = malloc( 1024 );
        scanf( "%1023s", argv[1] );

        printf( "  infile  -> " );
        argv[2] = malloc( 1024 );
        scanf( "%1023s", argv[2] );

        printf( "  outfile -> " );
        argv[3] = malloc( 1024 );
        scanf( "%1023s", argv[3] );

        printf( "  key     -> " );
        argv[4] = malloc( 1024 );
        scanf( "%1023s", argv[4] );

        printf( "\n" );
#else
        do_exit( 1 );
#endif
    }

    sscanf( argv[1], "%d", &mode );

    if( mode != MODE_ENCRYPT && mode != MODE_DECRYPT )
    {
        fprintf( stderr, "invalide mode \"%d\"\n", mode );
        do_exit( 1 );
    }

    if( ( fin = fopen( argv[2], "rb" ) ) == NULL )
    {
        fprintf( stderr, "fopen(%s,rb) failed\n", argv[2] );
        do_exit( 1 );
    }

    if( ! ( fout = fopen( argv[3], "wb" ) ) )
    {
        fprintf( stderr, "fopen(%s,wb) failed\n", argv[3] );
        do_exit( 1 );
    }

    /* read the secret key and clean the command line */

    memset( user_key, 0, sizeof( user_key ) );

    if( ( fkey = fopen( argv[4], "rb" ) ) != NULL )
    {
        fread( user_key, 1, sizeof( user_key ) - 1, fkey );
        fclose( fkey );
    }
    else
        strncpy( user_key, argv[4], sizeof( user_key ) - 1 );

    memset( argv[4], 0, strlen( argv[4] ) );

    /* read the input file size */

#ifndef WIN32
    if( ( filesize = lseek( fileno( fin ), 0, SEEK_END ) ) < 0 )
    {
        perror( "lseek" );
        return( 1 );
    }
#else
    {
        LARGE_INTEGER li_size;

        li_size.QuadPart = 0;
        li_size.LowPart  = SetFilePointer(
            (HANDLE) _get_osfhandle( fileno( fin ) ),
            li_size.LowPart, &li_size.HighPart, FILE_END );

        if( li_size.LowPart == -1 && GetLastError() != NO_ERROR )
        {
            fprintf( stderr, "SetFilePointer(0,FILE_END) failed\n" );
            do_exit( 1 );
        }

        filesize = li_size.QuadPart;
    }
#endif

    if( fseek( fin, 0, SEEK_SET ) < 0 )
    {
        fprintf( stderr, "fseek(0,SEEK_SET) failed\n" );
        do_exit( 1 );
    }

    if( mode == MODE_ENCRYPT )
    {
        /* compute the initialization vector as:     *
         * IV = SHA256( time + filesize + filename ) *
         * truncated to the AES block size (16)      */

        time_t cur_time = time( NULL );

        for( i = 0; i < 8; i++ )
            buffer[i    ] = (unsigned char) ( cur_time >> (i * 8) );

        for( i = 0; i < 8; i++ )
            buffer[i + 8] = (unsigned char) ( filesize >> (i * 8) );

        sha256_starts( &sha_ctx );
        sha256_update( &sha_ctx, buffer, 16 );
        sha256_update( &sha_ctx, (unsigned char *) argv[2],
                                           strlen( argv[2] ) );
        sha256_finish( &sha_ctx, digest );

        memcpy( IV, digest, 16 );

        /* four bits in the IV are actually used to store *
         * the file size modulo the AES block size (16)   */

        lastn = (int) ( filesize & 0x0F );

        IV[15] &= 0xF0;
        IV[15] |= lastn;

        /* append the IV at the beginning of the output */

        if( my_fwrite( fout, IV, 16 ) != 0 )
            do_exit( 1 );

        /* hash the IV and the secret key together 8192 times *
         * using the result to setup the AES context and HMAC */

        memset( digest, 0,  32 );
        memcpy( digest, IV, 16 );

        for( i = 0; i < 8192; i++ )
        {
            sha256_starts( &sha_ctx );
            sha256_update( &sha_ctx, digest, 32 );
            sha256_update( &sha_ctx, (unsigned char *) user_key,
                                               strlen( user_key ) );
            sha256_finish( &sha_ctx, digest );
        }

        memset( user_key, 0, sizeof( user_key ) );

        aes_set_key( &aes_ctx, digest, 256 );

        memset( k_ipad, 0x36, 64 );
        memset( k_opad, 0x5C, 64 );

        for( i = 0; i < 32; i++ )
        {
            k_ipad[i] ^= digest[i];
            k_opad[i] ^= digest[i];
        }

        /* encrypt and write the ciphertext */

        sha256_starts( &sha_ctx );
        sha256_update( &sha_ctx, k_ipad, 64 );

        for( offset = 0; offset < filesize; offset += 16 )
        {
            n = ( filesize - offset > 16 ) ? 16 : (int)
                ( filesize - offset );

            if( my_fread( fin, buffer, n ) != 0 )
                do_exit( 1 );

            for( i = 0; i < 16; i++ )
                buffer[i] ^= IV[i];

            aes_encrypt(   &aes_ctx, buffer, buffer );
            sha256_update( &sha_ctx, buffer, 16 );

            if( my_fwrite( fout, buffer, 16 ) != 0 )
                do_exit( 1 );

            memcpy( IV, buffer, 16 );
        }

        /* finally write the HMAC */

        sha256_finish( &sha_ctx, digest );

        sha256_starts( &sha_ctx );
        sha256_update( &sha_ctx, k_opad, 64 );
        sha256_update( &sha_ctx, digest, 32 );
        sha256_finish( &sha_ctx, digest );

        if( my_fwrite( fout, digest, 32 ) != 0 )
            do_exit( 1 );
    }

    if( mode == MODE_DECRYPT )
    {
        /*
         *  The encrypted file shall be structured as:
         *
         *  00 : 15                    Initialization Vector
         *  16 : 31                    AES Encrypted Block #1
         *  ...        ...
         *   N   *16 : (N+1)*16 - 1    AES Encrypted Block #N
         *  (N+1)*16 : (N+1)*16 + 32   HMAC-SHA256( Ciphertext )
         */

        if( filesize < 48 )
        {
            fprintf( stderr, "file too short to be encrypted!\n" );
            do_exit( 1 );
        }

        if( ( filesize & 0x0F ) != 0 )
        {
            fprintf( stderr, "file size not a multiple of 16!\n" );
            do_exit( 1 );
        }

        /* substract the IV + HMAC length */

        filesize -= ( 16 + 32 );

        /* read the IV and original filesize modulo 16 */

        if( my_fread( fin, buffer, 16 ) != 0 )
            do_exit( 1 );

        memcpy( IV, buffer, 16 );

        lastn = IV[15] & 0x0F;

        /* hash the IV and the secret key together 8192 times *
         * using the result to setup the AES context and HMAC */

        memset( digest, 0,  32 );
        memcpy( digest, IV, 16 );

        for( i = 0; i < 8192; i++ )
        {
            sha256_starts( &sha_ctx );
            sha256_update( &sha_ctx, digest, 32 );
            sha256_update( &sha_ctx, (unsigned char *) user_key,
                                               strlen( user_key ) );
            sha256_finish( &sha_ctx, digest );
        }

        memset( user_key, 0, sizeof( user_key ) );

        aes_set_key( &aes_ctx, digest, 256 );

        memset( k_ipad, 0x36, 64 );
        memset( k_opad, 0x5C, 64 );

        for( i = 0; i < 32; i++ )
        {
            k_ipad[i] ^= digest[i];
            k_opad[i] ^= digest[i];
        }

        /* now decrypt and write the plaintext */

        sha256_starts( &sha_ctx );
        sha256_update( &sha_ctx, k_ipad, 64 );

        for( offset = 0; offset < filesize; offset += 16 )
        {
            if( my_fread( fin, buffer, 16 ) != 0 )
                do_exit( 1 );

            memcpy( tmp, buffer, 16 );
 
            sha256_update( &sha_ctx, buffer, 16 );
            aes_decrypt(   &aes_ctx, buffer, buffer );
   
            for( i = 0; i < 16; i++ )
                buffer[i] ^= IV[i];

            memcpy( IV, tmp, 16 );

            n = ( lastn > 0 && offset == filesize - 16 )
                ? lastn : 16;

            if( my_fwrite( fout, buffer, n ) != 0 )
                do_exit( 1 );
        }

        /* verify the message authentication code */

        sha256_finish( &sha_ctx, digest );

        sha256_starts( &sha_ctx );
        sha256_update( &sha_ctx, k_opad, 64 );
        sha256_update( &sha_ctx, digest, 32 );
        sha256_finish( &sha_ctx, digest );

        if( my_fread( fin, buffer, 32 ) != 0 )
            do_exit( 1 );

        if( memcmp( digest, buffer, 32 ) != 0 )
        {
            fprintf( stderr, "HMAC check failed: wrong key, "
                             "or file corrupted.\n" );
            do_exit( 1 );
        }
    }

    return( 0 );
}
