// -*- C++ -*-
//
// generated by wxGlade
//
// Example for compiling a single file project under Linux using g++:
//  g++ MyApp.cpp $(wx-config --libs) $(wx-config --cxxflags) -o MyApp
//
// Example for compiling a multi file project under Linux using g++:
//  g++ main.cpp $(wx-config --libs) $(wx-config --cxxflags) -o MyApp Dialog1.cpp Frame1.cpp
//

#include "Grid.h"

// begin wxGlade: ::extracode
// end wxGlade



MyFrame::MyFrame(wxWindow* parent, wxWindowID id, const wxString& title, const wxPoint& pos, const wxSize& size, long style):
    wxFrame(parent, id, title, pos, size, wxDEFAULT_FRAME_STYLE)
{
    // begin wxGlade: MyFrame::MyFrame
    SetTitle(wxT("frame_1"));
    wxBoxSizer* sizer_1 = new wxBoxSizer(wxVERTICAL);
    grid_1 = new wxGrid(this, wxID_ANY);
    grid_1->CreateGrid(2, 2);
    grid_1->SetLabelFont(wxFont(14, wxMODERN, wxNORMAL, wxNORMAL, 0, wxT("")));
    grid_1->SetDefaultCellFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, wxT("")));
    grid_1->SetGridLineColour(wxColour(255, 0, 0));
    grid_1->SetLabelBackgroundColour(wxColour(216, 191, 216));
    grid_1->SetColLabelValue(0, wxT("Column A"));
    grid_1->SetColLabelValue(1, wxT("Column B"));
    grid_1->SetBackgroundColour(wxColour(0, 255, 255));
    grid_1->SetRowLabelValue(0, "Row 1");
    grid_1->SetCellValue(0, 0, "1");
    sizer_1->Add(grid_1, 1, wxEXPAND, 0);
    
    SetSizer(sizer_1);
    sizer_1->Fit(this);
    Layout();
    // end wxGlade
}


BEGIN_EVENT_TABLE(MyFrame, wxFrame)
    // begin wxGlade: MyFrame::event_table
    EVT_GRID_CMD_CELL_LEFT_CLICK(wxID_ANY, MyFrame::myEVT_GRID_CELL_LEFT_CLICK)
    // end wxGlade
END_EVENT_TABLE();


void MyFrame::myEVT_GRID_CELL_LEFT_CLICK(wxGridEvent &event)  // wxGlade: MyFrame.<event_handler>
{
    event.Skip();
    // notify the user that he hasn't implemented the event handler yet
    wxLogDebug(wxT("Event handler (MyFrame::myEVT_GRID_CELL_LEFT_CLICK) not implemented yet"));
}


// wxGlade: add MyFrame event handlers

