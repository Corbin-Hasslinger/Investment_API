import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ResearchSearchPage } from './research-search-page';

describe('ResearchSearchPage', () => {
  let component: ResearchSearchPage;
  let fixture: ComponentFixture<ResearchSearchPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResearchSearchPage],
    }).compileComponents();

    fixture = TestBed.createComponent(ResearchSearchPage);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
