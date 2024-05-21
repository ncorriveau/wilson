import { extendTheme } from "@chakra-ui/react";

const customTheme = extendTheme({
  colors: {
    green: {
      800: "#2F855A",
      700: "#38A169",
    },
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: "bold",
        color: "white",
      },
      sizes: {
        lg: {
          h: "48px",
          fontSize: "lg",
          px: "32px",
        },
      },
      variants: {
        solid: (props: any) => ({
          bg: props.colorScheme === "green" ? "green.800" : undefined,
          color: "white",
          _hover: {
            bg: props.colorScheme === "green" ? "green.700" : undefined,
          },
        }),
      },
    },
    Heading: {
      baseStyle: {
        fontFamily: "serif",
        color: "green.800",
      },
    },
  },
});

export default customTheme;
