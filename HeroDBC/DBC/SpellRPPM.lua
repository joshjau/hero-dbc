-- Generated using WoW 11.0.7.58867 client data on 2025-02-01T14:09:28.014626.
--- ============================ HEADER ============================
--- Optimized SpellRPPM table for DPS calculations
--- Format: [spellID] = { base = ppm, type = "damage"|"stat"|"utility", mods = {...} }
HeroDBC.DBC.SpellRPPM = {
  -- Damage Procs
  [1] = {
    base = 4.0,
    type = "damage",
    mods = {
      class_520 = 1.5,
      crit = true,
      haste = true,
    },
  },
  [38] = {
    base = 1.74,
    type = "damage",
    mods = {
      haste = true,
      spec_103 = 0.3,
      spec_104 = -0.4,
      spec_250 = -0.4,
      spec_251 = 0.5,
      spec_252 = 0.05,
      spec_253 = 0.0,
      spec_254 = 0.2,
      spec_255 = 0.15,
      spec_259 = 0.55,
      spec_260 = 0.15,
      spec_261 = 0.0,
      spec_263 = 0.55,
      spec_268 = -0.4,
      spec_269 = 0.2,
      spec_66 = -0.4,
      spec_70 = 0.45,
      spec_71 = 0.35,
      spec_72 = 0.05,
      spec_73 = -0.4,
    },
  },
  [39] = {
    base = 2.611,
    type = "damage",
    mods = {
      haste = true,
      spec_102 = 0.1,
      spec_104 = -0.75,
      spec_250 = -0.75,
      spec_258 = 0.0,
      spec_262 = 0.05,
      spec_265 = 0.1,
      spec_266 = 0.25,
      spec_267 = 0.15,
      spec_268 = -0.75,
      spec_62 = 0.25,
      spec_63 = 0.2,
      spec_64 = 0.2,
      spec_66 = -0.75,
      spec_73 = -0.75,
    },
  },
  [41] = {
    base = 0.96,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [42] = {
    base = 1.64,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [43] = {
    base = 2.89,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [44] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [50] = {
    base = 2.57,
    type = "damage",
  },
  [51] = {
    base = 19.27,
    type = "damage",
    mods = {
      haste = true,
      spec_103 = 0.721,
      spec_104 = -0.4,
      spec_250 = -0.4,
      spec_251 = 0.532,
      spec_252 = -0.162,
      spec_253 = -0.05,
      spec_254 = 0.107,
      spec_255 = -0.05,
      spec_259 = 0.789,
      spec_260 = 0.136,
      spec_261 = 0.114,
      spec_263 = -0.191,
      spec_268 = -0.4,
      spec_269 = 0.087,
      spec_66 = -0.4,
      spec_70 = 0.295,
      spec_71 = 0.339,
      spec_72 = 0.257,
      spec_73 = -0.4,
    },
  },
  [54] = {
    base = 1.61,
    type = "damage",
  },
  [55] = {
    base = 1.35,
    type = "damage",
    mods = {
      spec_102 = 0.872,
      spec_258 = -0.067,
      spec_262 = 0.891,
      spec_265 = -0.375,
      spec_266 = -0.402,
      spec_267 = -0.491,
      spec_62 = -0.239,
      spec_63 = -0.295,
      spec_64 = 0.387,
    },
  },
  [57] = {
    base = 1.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [58] = {
    base = 1.1,
    type = "damage",
  },
  [59] = {
    base = 5.78,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [60] = {
    base = 0.72,
    type = "damage",
    mods = {
      crit = true,
    },
  },
  [61] = {
    base = 0.58,
    type = "damage",
    mods = {
      class_256 = -0.4,
      spec_102 = -0.35,
    },
  },
  [62] = {
    base = 0.85,
    type = "damage",
    mods = {
      crit = true,
    },
  },
  [63] = {
    base = 9.17,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [64] = {
    base = 3.67,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [66] = {
    base = 5.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [72] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [73] = {
    base = 2.0,
    type = "damage",
    mods = {
      crit = true,
    },
  },
  [74] = {
    base = 2.0,
    type = "damage",
    mods = {
      class_1152 = 0.5,
    },
  },
  [75] = {
    base = 2.0,
    type = "damage",
    mods = {
      race_72 = 0.5,
    },
  },
  [80] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [81] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [84] = {
    base = 0.92,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [97] = {
    base = 1.1,
    type = "damage",
    mods = {
      spec_72 = -0.625,
    },
  },
  [99] = {
    base = 2.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [100] = {
    base = 3.75,
    type = "damage",
    mods = {
      haste = true,
      spec_262 = 0.0,
      spec_263 = 0.0,
      spec_264 = 0.0,
    },
  },
  [101] = {
    base = 2.0,
    type = "damage",
  },
  [103] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [104] = {
    base = 1.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [108] = {
    base = 2.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [112] = {
    base = 1.25,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [113] = {
    base = 1.0,
    type = "damage",
    mods = {
      class_512 = -0.1,
      class_8 = 0.1,
    },
  },
  [114] = {
    base = 0.85,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [116] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [117] = {
    base = 5.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [118] = {
    base = 5.0,
    type = "damage",
    mods = {
      haste = true,
      spec_258 = -0.167,
      spec_62 = -0.4,
    },
  },
  [119] = {
    base = 1.5,
    type = "damage",
    mods = {
      spec_258 = -0.167,
      spec_62 = -0.4,
    },
  },
  [121] = {
    base = 1.7,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [122] = {
    base = 3.0,
    type = "damage",
    mods = {
      class_2012 = 0.005,
      haste = true,
    },
  },
  [124] = {
    base = 6.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [127] = {
    base = 20.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [129] = {
    base = 4.5,
    type = "damage",
    mods = {
      crit = true,
      haste = true,
    },
  },
  [130] = {
    base = 2.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [132] = {
    base = 7.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [133] = {
    base = 1.1,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [137] = {
    base = 20.0,
    type = "damage",
    mods = {
      spec_0 = 0.0,
    },
  },
  [141] = {
    base = 3.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [142] = {
    base = 20.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [143] = {
    base = 8.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [144] = {
    base = 4.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [145] = {
    base = 0.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [148] = {
    base = 1.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [150] = {
    base = 1.25,
    type = "damage",
    mods = {
      class_32 = -0.32,
      haste = true,
    },
  },
  [151] = {
    base = 6.0,
    type = "damage",
    mods = {
      crit = true,
    },
  },
  [154] = {
    base = 6.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [157] = {
    base = 6.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [158] = {
    base = 3.0,
    type = "damage",
    mods = {
      spec_103 = 1.24,
      spec_251 = 1.2,
      spec_252 = 1.8,
      spec_253 = 1.8,
      spec_254 = 1.24,
      spec_255 = 0.5,
      spec_259 = 0.17,
      spec_260 = 1.8,
      spec_261 = 2.0,
      spec_263 = 2.0,
      spec_269 = -0.2,
      spec_577 = 0.12,
      spec_70 = 0.0,
      spec_71 = 0.1,
      spec_72 = 0.72,
    },
  },
  [159] = {
    base = 0.85,
    type = "damage",
    mods = {
      class_35 = -0.5,
      haste = true,
    },
  },
  [160] = {
    base = 4.0,
    type = "damage",
    mods = {
      haste = true,
      spec_263 = -0.24,
    },
  },
  [161] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
      spec_253 = -0.27,
      spec_263 = -0.24,
    },
  },
  [162] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [163] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
      spec_263 = -0.24,
    },
  },
  [164] = {
    base = 1.0,
    type = "damage",
    mods = {
      spec_252 = -0.32,
    },
  },
  [165] = {
    base = 12.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [166] = {
    base = 0.75,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [168] = {
    base = 20.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [169] = {
    base = 2.0,
    type = "damage",
    mods = {
      class_35 = -0.5,
      haste = true,
    },
  },
  [170] = {
    base = 12.0,
    type = "damage",
    mods = {
      crit = true,
    },
  },
  [171] = {
    base = 0.7,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [179] = {
    base = 4.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [180] = {
    base = 0.92,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [181] = {
    base = 2.0,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_256 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [182] = {
    base = 1.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [184] = {
    base = 1.2,
    type = "damage",
    mods = {
      haste = true,
      spec_105 = 0.12,
      spec_256 = -0.24,
      spec_257 = 0.18,
      spec_264 = 0.12,
      spec_270 = 0.03,
      spec_65 = -0.13,
    },
  },
  [186] = {
    base = 4.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [187] = {
    base = 1.5,
    type = "damage",
    mods = {
      haste = true,
      spec_252 = -0.32,
    },
  },
  [188] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
      spec_263 = -0.24,
    },
  },
  [189] = {
    base = 1.0,
    type = "damage",
    mods = {
      haste = true,
      spec_252 = -0.32,
    },
  },
  [190] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
      spec_263 = -0.24,
    },
  },
  [191] = {
    base = 1.0,
    type = "damage",
    mods = {
      haste = true,
      spec_253 = -0.27,
    },
  },
  [192] = {
    base = 0.92,
    type = "damage",
    mods = {
      crit = true,
    },
  },
  [195] = {
    base = 4.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [198] = {
    base = 2.25,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [199] = {
    base = 1.0,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [200] = {
    base = 1.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_253 = -0.5,
      spec_254 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [201] = {
    base = 1.0,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [202] = {
    base = 1.0,
    type = "damage",
    mods = {
      class_476 = -0.5,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_105 = -0.5,
      spec_251 = -0.5,
      spec_252 = -0.5,
      spec_269 = -0.5,
      spec_270 = -0.5,
      spec_577 = -0.5,
      spec_65 = -0.5,
      spec_70 = -0.5,
      spec_71 = -0.5,
      spec_72 = -0.5,
    },
  },
  [203] = {
    base = 2.0,
    type = "damage",
    mods = {
      class_4060 = -0.5,
      haste = true,
      spec_250 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [204] = {
    base = 12.0,
    type = "damage",
    mods = {
      class_2607 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [205] = {
    base = 5.0,
    type = "damage",
    mods = {
      class_435 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_253 = -0.5,
      spec_254 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
    },
  },
  [206] = {
    base = 3.0,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [207] = {
    base = 0.7,
    type = "damage",
    mods = {
      class_400 = -0.5,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [208] = {
    base = 1.5,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [209] = {
    base = 1.0,
    type = "damage",
    mods = {
      class_435 = -0.5,
      class_8 = -0.3,
      spec_102 = -0.5,
      spec_103 = -0.3,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_253 = 1.0,
      spec_254 = 1.0,
      spec_255 = 1.5,
      spec_262 = -0.5,
      spec_263 = 0.0,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_269 = 0.0,
      spec_270 = -0.5,
      spec_577 = 0.0,
      spec_581 = -0.5,
    },
  },
  [210] = {
    base = 2.0,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [211] = {
    base = 2.0,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [212] = {
    base = 3.0,
    type = "damage",
    mods = {
      class_2607 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [213] = {
    base = 0.7,
    type = "damage",
    mods = {
      class_2607 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [214] = {
    base = 2.0,
    type = "damage",
    mods = {
      class_2093 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [215] = {
    base = 3.5,
    type = "damage",
    mods = {
      class_435 = -0.5,
      haste = true,
    },
  },
  [216] = {
    base = 1.8,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [217] = {
    base = 1.5,
    type = "damage",
    mods = {
      class_476 = -0.5,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_105 = -0.5,
      spec_251 = -0.5,
      spec_252 = -0.5,
      spec_269 = -0.5,
      spec_270 = -0.5,
      spec_577 = -0.5,
      spec_65 = -0.5,
      spec_70 = -0.5,
      spec_71 = -0.5,
      spec_72 = -0.5,
    },
  },
  [218] = {
    base = 10.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_253 = -0.5,
      spec_254 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [219] = {
    base = 1.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_253 = -0.5,
      spec_254 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [220] = {
    base = 6.0,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [221] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [222] = {
    base = 1.5,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [224] = {
    base = 2.0,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [225] = {
    base = 1.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [226] = {
    base = 3.0,
    type = "damage",
    mods = {
      class_476 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_105 = -0.5,
      spec_251 = -0.5,
      spec_252 = -0.5,
      spec_269 = -0.5,
      spec_270 = -0.5,
      spec_577 = -0.5,
      spec_65 = -0.5,
      spec_70 = -0.5,
      spec_71 = -0.5,
      spec_72 = -0.5,
    },
  },
  [227] = {
    base = 4.0,
    type = "damage",
    mods = {
      class_476 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_105 = -0.5,
      spec_251 = -0.5,
      spec_252 = -0.5,
      spec_269 = -0.5,
      spec_270 = -0.5,
      spec_577 = -0.5,
      spec_65 = -0.5,
      spec_70 = -0.5,
      spec_71 = -0.5,
      spec_72 = -0.5,
    },
  },
  [228] = {
    base = 1.2,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [230] = {
    base = 2.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [232] = {
    base = 1.0,
    type = "damage",
    mods = {
      haste = true,
      spec_253 = -0.27,
    },
  },
  [235] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [236] = {
    base = 8.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [237] = {
    base = 22.0,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [238] = {
    base = 1.2,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [239] = {
    base = 0.65,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [240] = {
    base = 26.667,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [241] = {
    base = 4.0,
    type = "damage",
    mods = {
      haste = true,
      spec_252 = -0.32,
    },
  },
  [242] = {
    base = 3.0,
    type = "damage",
    mods = {
      class_476 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_105 = -0.5,
      spec_251 = -0.5,
      spec_252 = -0.5,
      spec_269 = -0.5,
      spec_270 = -0.5,
      spec_577 = -0.5,
      spec_65 = -0.5,
      spec_70 = -0.5,
      spec_71 = -0.5,
      spec_72 = -0.5,
    },
  },
  [244] = {
    base = 4.0,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [246] = {
    base = 9.0,
    type = "damage",
    mods = {
      class_2089 = -0.5,
      crit = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_255 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [247] = {
    base = 1.7,
    type = "damage",
    mods = {
      class_2603 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_255 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [248] = {
    base = 10.0,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [249] = {
    base = 3.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [250] = {
    base = 3.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [251] = {
    base = 7.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [252] = {
    base = 3.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_253 = -0.5,
      spec_254 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [253] = {
    base = 10.0,
    type = "damage",
    mods = {
      class_400 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_250 = -0.5,
      spec_253 = -0.5,
      spec_254 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [254] = {
    base = 1.8,
    type = "damage",
    mods = {
      spec_71 = -0.4,
    },
  },
  [255] = {
    base = 5.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [256] = {
    base = 4.0,
    type = "damage",
    mods = {
      class_2607 = -0.5,
      haste = true,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [257] = {
    base = 10.0,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [258] = {
    base = 1.4,
    type = "damage",
    mods = {
      class_476 = -0.5,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_105 = -0.5,
      spec_251 = -0.5,
      spec_252 = -0.5,
      spec_269 = -0.5,
      spec_270 = -0.5,
      spec_577 = -0.5,
      spec_65 = -0.5,
      spec_70 = -0.5,
      spec_71 = -0.5,
      spec_72 = -0.5,
    },
  },
  [260] = {
    base = 1.8,
    type = "damage",
    mods = {
      class_435 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_262 = -0.5,
      spec_264 = -0.5,
      spec_268 = -0.5,
      spec_270 = -0.5,
      spec_581 = -0.5,
    },
  },
  [261] = {
    base = 1.2,
    type = "damage",
    mods = {
      class_2477 = -0.5,
      haste = true,
      spec_102 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_258 = -0.5,
      spec_262 = -0.5,
      spec_263 = -0.5,
      spec_268 = -0.5,
      spec_269 = -0.5,
      spec_66 = -0.5,
      spec_70 = -0.5,
    },
  },
  [262] = {
    base = 1.4,
    type = "damage",
    mods = {
      class_4060 = -0.5,
      spec_250 = -0.5,
      spec_65 = -0.5,
      spec_66 = -0.5,
      spec_73 = -0.5,
    },
  },
  [263] = {
    base = 1.4,
    type = "damage",
    mods = {
      class_2607 = -0.5,
      spec_103 = -0.5,
      spec_104 = -0.5,
      spec_105 = -0.5,
      spec_257 = -0.5,
      spec_263 = -0.5,
      spec_264 = -0.5,
    },
  },
  [264] = {
    base = 0.25,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [265] = {
    base = 0.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [266] = {
    base = 20.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [269] = {
    base = 5.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [271] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [272] = {
    base = 4.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [273] = {
    base = 1.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [275] = {
    base = 1.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [276] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [277] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [279] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [280] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [383] = {
    base = 1.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [385] = {
    base = 10.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [386] = {
    base = 6.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [388] = {
    base = 10.8,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [392] = {
    base = 2.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [394] = {
    base = 1.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [395] = {
    base = 9.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [397] = {
    base = 0.35,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [399] = {
    base = 6.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [400] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [403] = {
    base = 10.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [404] = {
    base = 10.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [405] = {
    base = 40.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [406] = {
    base = 1.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [407] = {
    base = 1.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [408] = {
    base = 1.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [409] = {
    base = 2.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [410] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [411] = {
    base = 1.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [412] = {
    base = 15.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [413] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
      spec_105 = 0.4,
      spec_256 = 0.4,
      spec_257 = 0.4,
      spec_264 = 0.4,
      spec_270 = 0.4,
      spec_65 = 0.4,
    },
  },
  [414] = {
    base = 0.95,
    type = "damage",
    mods = {
      spec_65 = -0.2,
    },
  },
  [415] = {
    base = 0.5,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [422] = {
    base = 1.7,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [425] = {
    base = 3.0,
    type = "damage",
  },
  [426] = {
    base = 1.66,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [428] = {
    base = 1.3,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [430] = {
    base = 4.2,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [436] = {
    base = 50.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [438] = {
    base = 10.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [443] = {
    base = 30.0,
    type = "damage",
    mods = {
      spec_0 = 0.0,
    },
  },
  [445] = {
    base = 1.58,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [446] = {
    base = 3.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [449] = {
    base = 30.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [450] = {
    base = 7.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [452] = {
    base = 8.0,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  [453] = {
    base = 1.15,
    type = "damage",
    mods = {
      haste = true,
    },
  },
  -- Utility Procs
  [35] = {
    base = 0.581,
    type = "utility",
    mods = {
      spec_104 = -0.75,
      spec_105 = -0.2,
      spec_250 = -0.75,
      spec_256 = 0.4,
      spec_257 = 0.0,
      spec_264 = -0.3,
      spec_268 = -0.75,
      spec_270 = -0.2,
      spec_65 = 0.1,
      spec_66 = -0.75,
      spec_73 = -0.75,
    },
  },
}
