
import React from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Home,
  FileText,
  Wallet,
  Image,
  Info,
  Github,
  User,
  LogIn,
  LogOut,
  Settings,
  Moon,
  Sun,
} from "lucide-react";
import { useTheme } from "@/hooks/use-theme";
import MobileNav from "./MobileNav";
import { cn } from "@/lib/utils";

const Header = () => {
  const { theme, setTheme } = useTheme();

  const navItems = [
    { name: "Home", path: "/", icon: Home },
    { name: "Transactions", path: "/transactions", icon: FileText },
    { name: "NFT Minting", path: "/nft-minting", icon: Image },
    { name: "Wallet", path: "/wallet", icon: Wallet },
    { name: "About", path: "/about", icon: Info },
  ];

  return (
    <header className="w-full sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b">
      <div className="container mx-auto flex items-center justify-between h-16 px-4 md:px-6">
        <div className="flex items-center gap-6">
          <Link
            to="/"
            className="flex items-center gap-2 transition-transform hover:scale-105"
          >
            <div className="size-8 rounded-full algo-gradient flex items-center justify-center">
              <span className="font-bold text-white text-sm">AI</span>
            </div>
            <span className="text-lg font-bold algo-text-gradient">
              Algo-Intent
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-4">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-md hover:bg-accent"
              >
                <item.icon className="size-4" />
                {item.name}
              </Link>
            ))}
            <a
              href="https://github.com/caerlower/algo-intent"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-md hover:bg-accent"
            >
              <Github className="size-4" />
              GitHub
            </a>
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="rounded-full"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun className="size-4" />
            ) : (
              <Moon className="size-4" />
            )}
          </Button>

          <div className="hidden md:block">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full">
                  <User className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <User className="mr-2 size-4" /> Profile
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 size-4" /> Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <LogIn className="mr-2 size-4" /> Login
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <LogOut className="mr-2 size-4" /> Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="md:hidden">
            <MobileNav items={navItems} />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
