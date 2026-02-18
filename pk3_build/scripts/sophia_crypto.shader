// Sophia Crypto Hologram - more ghostly/ethereal
models/sophia_crypto_fixed/Material_0
{
    cull none
    deformVertexes wave 100 sin 0 0.5 0 0.5
    {
        map models/sophia_crypto_fixed/Material_0.png
        blendfunc GL_SRC_ALPHA GL_ONE
        alphaGen const 0.4
        rgbGen const ( 0.4 0.7 1.0 )
        tcMod scroll 0 0.02
    }
}
