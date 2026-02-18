// Sophia Hologram NPC - glowing blue transparent effect
models/sophia_hologram/Material_0
{
    cull none
    {
        map models/sophia_hologram/Material_0.png
        blendfunc add
        rgbGen const ( 0.3 0.6 1.0 )
    }
    {
        map models/sophia_hologram/Material_0.png
        blendfunc blend
        alphaGen const 0.6
        rgbGen const ( 0.5 0.8 1.0 )
    }
}
