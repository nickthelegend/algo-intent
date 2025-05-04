
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  LogIn,
  LogOut,
  Menu,
  Settings,
  User,
  Github,
} from "lucide-react";

type NavItem = {
  name: string;
  path: string;
  icon: React.ElementType;
};

interface MobileNavProps {
  items: NavItem[];
}

const MobileNav: React.FC<MobileNavProps> = ({ items }) => {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="size-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="flex flex-col">
        <SheetHeader>
          <SheetTitle>
            <Link
              to="/"
              className="flex items-center gap-2"
              onClick={() => setOpen(false)}
            >
              <div className="size-8 rounded-full algo-gradient flex items-center justify-center">
                <span className="font-bold text-white text-sm">AI</span>
              </div>
              <span className="text-xl font-bold algo-text-gradient">
                Algo-Intent
              </span>
            </Link>
          </SheetTitle>
        </SheetHeader>
        <div className="flex flex-col gap-3 mt-8">
          {items.map((item) => (
            <Link
              key={item.name}
              to={item.path}
              className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-accent transition-colors"
              onClick={() => setOpen(false)}
            >
              <item.icon className="size-5" />
              {item.name}
            </Link>
          ))}
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-accent transition-colors"
          >
            <Github className="size-5" />
            GitHub
          </a>
        </div>
        <div className="mt-auto flex flex-col gap-1 pt-4 border-t">
          <Button variant="ghost" className="justify-start gap-2" size="sm">
            <User className="size-4" />
            Profile
          </Button>
          <Button variant="ghost" className="justify-start gap-2" size="sm">
            <Settings className="size-4" />
            Settings
          </Button>
          <Button variant="ghost" className="justify-start gap-2" size="sm">
            <LogIn className="size-4" />
            Login
          </Button>
          <Button variant="ghost" className="justify-start gap-2" size="sm">
            <LogOut className="size-4" />
            Logout
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default MobileNav;
