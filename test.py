from chatbridgee.utils.format import dcToMcFormatting

print(dcToMcFormatting("~~awa~~"))  # §mawa§r
print(dcToMcFormatting("~~_awa_~~"))  # §m§nawa§r
print(dcToMcFormatting("_~~awa~~_"))  # §n§mawa§r
print(dcToMcFormatting("**~~awa~~**"))  # §o§mawa§r
print(dcToMcFormatting("***~~awa~~***"))  # §o§l§mawa§r
